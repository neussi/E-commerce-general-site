from decimal import Decimal
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import  UserRegisterForm , ProductUpdateForm, ProductForm
from decimal import Decimal
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import *
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import paypalrestsdk
import qrcode
from reportlab.platypus import Image  
from reportlab.lib.utils import ImageReader  

from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ContactForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# Configurer PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})



def home(request):
    # Récupérer les derniers produits ajoutés
    latest_products = Product.objects.select_related('owner').order_by('-created_at')[:8]
    
    # Récupérer les produits les plus populaires (à adapter selon vos besoins)
    popular_products = Product.objects.select_related('owner').order_by('?')[:6]
    
    # Récupérer quelques produits en vedette (random pour l'exemple)
    featured_products = Product.objects.select_related('owner').order_by('?')[:4]
    
    context = {
        'latest_products': latest_products,
        'popular_products': popular_products,
        'featured_products': featured_products,
    }
    return render(request, 'index.html', context)



def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = request.POST.get('role')
            user.save()
            login(request, user)
            return redirect('catalogue')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('catalogue')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login')
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            return redirect('catalogue')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

@login_required(login_url='/login')
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    if request.method == "POST":
        form = ProductUpdateForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProductUpdateForm(instance=product)
    return render(request, 'update_product.html', {'form': form, 'product': product})

@login_required(login_url='/login')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    if request.method == "POST":
        product.delete()
        return redirect('home')
    return render(request, 'delete_product.html', {'product': product})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})

def catalogue(request):
    # Récupérer le terme de recherche
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'recent')  # Par défaut, tri par date
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    # Construire la requête de base
    products = Product.objects.all()

    # Appliquer les filtres de recherche
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(owner__username__icontains=query)
        )

    # Filtre par prix
    if min_price:
        products = products.filter(price__gte=float(min_price))
    if max_price:
        products = products.filter(price__lte=float(max_price))

    # Appliquer le tri
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'recent':
        products = products.order_by('-created_at')
    elif sort == 'name':
        products = products.order_by('name')

    context = {
        'products': products,
        'current_query': query,
        'current_sort': sort,
        'current_min_price': min_price,
        'current_max_price': max_price,
    }

    return render(request, 'catalogue.html', context)




def user_profile(request, user_id):
    # Récupérer l'utilisateur ou renvoyer une erreur 404 si non trouvé
    user = get_object_or_404(User, id=user_id)
    
    
    # Récupérer les produits de l'utilisateur
    products = Product.objects.filter(owner=user)
    total_products = products.count()
    
    # Récupérer les commandes liées à l'utilisateur
    if user.role == 'farmer':
        # Si l'utilisateur est un agriculteur, compter les commandes de ses produits
        total_orders = Order.objects.filter(product__owner=user).count()
    else:
        # Si l'utilisateur est un acheteur ou fournisseur, compter ses commandes
        total_orders = Order.objects.filter(buyer=user).count()
    
    # Contexte pour le template
    context = {
        'user': user,
        'total_products': total_products,
        'total_orders': total_orders,
        'products': products,
    }
    
    return render(request, 'user_profile.html', context)





def payment_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'payment/payment.html', {
        'product': product,
        'paypal_client_id': 'VOTRE_CLIENT_ID'
    })


# Ajoutez ces fonctions à votre fichier views.py

@login_required(login_url='/login')
def handle_cart_payment(request):
    if request.method == 'POST':
        try:
            # Récupérer le panier de l'utilisateur
            cart = Cart.objects.get(user=request.user, ordered=False)
            cart_items = cart.items.all()
            
            if not cart_items.exists():
                messages.warning(request, "Votre panier est vide.")
                return redirect('cart')
            
            # Pour PayPal (AJAX request)
            if request.content_type == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
                
                # Créer une commande principale
                order = Order.objects.create(
                    buyer=request.user,
                    total_amount=float(data.get('total_amount', cart.get_total_price())),
                    payment_id=data.get('paypal_order_id', f'SIM-{uuid.uuid4()}'),
                    buyer_email=data.get('email', request.user.email),
                    status='COMPLETED'
                )
                
                # Ajouter les détails des articles commandés
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                        total=item.get_total_item_price()
                    )
                
                # Créer un enregistrement de paiement
                payment_method = data.get('payment_method', 'simulated')
                Payment.objects.create(
                    order=order,
                    amount=float(data.get('total_amount', cart.get_total_price())),
                    payment_method=payment_method,
                    transaction_id=data.get('paypal_order_id', order.payment_id),
                    status='completed'
                )
                
                # Marquer le panier comme commandé
                cart_items.update(ordered=True)
                cart.ordered = True
                cart.save()
                
                return JsonResponse({
                    'success': True, 
                    'order_id': order.id,
                    'redirect_url': reverse('payment_success') + f'?order_id={order.id}'
                })
            
            # Pour paiement normal (form submit)
            else:
                # Créer une commande principale
                order = Order.objects.create(
                    buyer=request.user,
                    total_amount=float(request.POST.get('total_amount', cart.get_total_price())),
                    payment_id=f'NORMAL-{uuid.uuid4()}',
                    buyer_email=request.user.email,
                    status='COMPLETED'
                )
                
                # Ajouter les détails des articles commandés
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price,
                        total=item.get_total_item_price()
                    )
                
                # Créer un enregistrement de paiement
                Payment.objects.create(
                    order=order,
                    amount=float(request.POST.get('total_amount', cart.get_total_price())),
                    payment_method=request.POST.get('payment_method', 'normal'),
                    transaction_id=order.payment_id,
                    status='completed'
                )
                
                # Marquer le panier comme commandé
                cart_items.update(ordered=True)
                cart.ordered = True
                cart.save()
                
                return redirect(f'/payment/success/?order_id={order.id}')
                
        except Cart.DoesNotExist:
            messages.error(request, "Vous n'avez pas de panier actif.")
            return redirect('catalogue')
        except Exception as e:
            messages.error(request, f'Erreur lors du paiement: {str(e)}')
            return redirect('cart')
    
    return redirect('cart')

def payment_success(request):
    order_id = request.GET.get('order_id')
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        return render(request, 'payment_success.html', {'order': order})
    except Order.DoesNotExist:
        messages.error(request, "Commande introuvable.")
        return redirect('catalogue')  

def download_invoice(request, order_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Image, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    import qrcode
    from io import BytesIO
    
    order = get_object_or_404(Order, id=order_id)
    buffer = BytesIO()
    
    # Configuration de la page
    width, height = A4
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        alignment=1,  # Center
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leading=14
    )
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.black,
        spaceBefore=12,
        spaceAfter=6
    )
    
    # Couleurs de l'entreprise
    orange_color = colors.Color(1, 0.5, 0)  # Orange
    black_color = colors.black
    
    # En-tête avec logo et infos entreprise
    # Bordure orange en haut
    p.setStrokeColor(orange_color)
    p.setLineWidth(5)
    p.line(1*cm, height-1*cm, width-1*cm, height-1*cm)
    
    # Logo (simulé par un rectangle avec texte)
    p.setFillColor(orange_color)
    p.rect(1.5*cm, height-4*cm, 3*cm, 2*cm, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(3*cm, height-3*cm, "KF")
    
    # Informations entreprise
    p.setFillColor(black_color)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(5*cm, height-2.3*cm, "KmerFusion")
    p.setFont("Helvetica", 10)
    p.drawString(5*cm, height-2.8*cm, "123 Avenue Principale, Yaoundé, Cameroun")
    p.drawString(5*cm, height-3.3*cm, "www.kmerfusion.com | support@kmerfusion.com")
    p.drawString(5*cm, height-3.8*cm, "Tél: +237 123 456 789 | RCCM: 12345-CAM-2023")
    
    # Titre Facture
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height-5.5*cm, "FACTURE")
    
    # Numéro et date de facture
    p.setFillColor(orange_color)
    p.rect(width-6*cm, height-5*cm, 4.5*cm, 3*cm, fill=0)
    p.setFillColor(black_color)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(width-5.8*cm, height-2.5*cm, "N° Facture:")
    p.drawString(width-5.8*cm, height-3*cm, "Date:")
    p.drawString(width-5.8*cm, height-3.5*cm, "Réf:")
    p.setFont("Helvetica", 10)
    p.drawString(width-3.5*cm, height-2.5*cm, f"F-{order.id:06d}")
    p.drawString(width-3.5*cm, height-3*cm, f"{order.created_at.strftime('%d/%m/%Y')}")
    p.drawString(width-3.5*cm, height-3.5*cm, f"CD-{order.id:06d}")
    
    # Informations client
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1.5*cm, height-7*cm, "Informations client")
    p.setStrokeColor(orange_color)
    p.setLineWidth(1)
    p.line(1.5*cm, height-7.2*cm, 6*cm, height-7.2*cm)
    
    # Cadre client
    p.setStrokeColor(colors.lightgrey)
    p.rect(1.5*cm, height-10*cm, 8*cm, 2.5*cm, fill=0)
    
    p.setFont("Helvetica", 10)
    y_position = height - 7.8*cm
    p.drawString(2*cm, y_position, f"Nom: {order.buyer.username}")
    y_position -= 0.5*cm
    p.drawString(2*cm, y_position, f"Email: {order.buyer_email}")
    
    if hasattr(order.buyer, 'phone') and order.buyer.phone:
        y_position -= 0.5*cm
        p.drawString(2*cm, y_position, f"Téléphone: {order.buyer.phone}")
    
    if hasattr(order.buyer, 'numero_cni') and order.buyer.numero_cni:
        y_position -= 0.5*cm
        p.drawString(2*cm, y_position, f"CNI: {order.buyer.numero_cni}")
    
    # Générer QR code (contient le lien vers la facture)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4,
    )
    qr.add_data(f"https://kmerfusion.com/facture/{order.id}")
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    qr_buffer.seek(0)
    
    # Placer le QR code
    p.drawImage(ImageReader(qr_buffer), width-4.5*cm, height-10*cm, width=3*cm, height=3*cm)
    p.setFont("Helvetica", 8)
    p.drawCentredString(width-3*cm, height-10.5*cm, "Scannez pour vérifier")
    
    # Détails de la commande - Tableau
    data = [
        ["Description", "Quantité", "Prix unitaire", "Total"]
    ]
    
    # Vérifier si c'est une commande standard ou multi-produits
    if hasattr(order, 'items') and order.items.exists():
        # Commande multi-produits du panier
        for item in order.items.all():
            data.append([
                item.product.name,
                str(item.quantity),
                f"{item.price:,} FCFA".replace(',', ' '),
                f"{item.total:,} FCFA".replace(',', ' ')
            ])
    elif order.product:
        # Commande d'un seul produit
        data.append([
            order.product.name,
            str(order.quantity),
            f"{order.product.price:,} FCFA".replace(',', ' '),
            f"{order.total_amount:,} FCFA".replace(',', ' ')
        ])
    
    # Ajouter des lignes vides pour un meilleur aspect
    empty_rows_needed = max(0, 4 - len(data))
    for _ in range(empty_rows_needed):
        data.append(["", "", "", ""])
    
    table = Table(data, colWidths=[9*cm, 2*cm, 3.5*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    table.wrapOn(p, width, height)
    table.drawOn(p, 1.5*cm, height-15*cm)
    
    # Résumé des coûts
    p.setFont("Helvetica-Bold", 10)
    p.drawString(11.5*cm, height-16*cm, "Sous-total:")
    p.drawString(11.5*cm, height-16.7*cm, "TVA (0%):")
    p.drawString(11.5*cm, height-18*cm, "Montant total:")  # Position descendue pour laisser de l'espace

    p.setFont("Helvetica", 10)
    p.drawRightString(width-1.5*cm, height-16*cm, f"{order.total_amount:,} FCFA".replace(',', ' '))
    p.drawRightString(width-1.5*cm, height-16.7*cm, "0 FCFA")

    # Rectangle coloré pour le montant total (déplacé pour éviter le chevauchement avec la TVA)
    p.setFillColor(orange_color)
    p.rect(11*cm, height-18.5*cm, width-12.5*cm, 1*cm, fill=1)  # Position ajustée
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    # Position du texte ajustée pour être au milieu du rectangle
    p.drawRightString(width-1.5*cm, height-17.9*cm, f"{order.total_amount:,} FCFA".replace(',', ' '))  
    
    # Informations de paiement
    p.setFillColor(black_color)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1.5*cm, height-18.5*cm, "Informations de paiement")
    p.setStrokeColor(orange_color)
    p.line(1.5*cm, height-18.7*cm, 7*cm, height-18.7*cm)
    
    p.setFont("Helvetica", 10)
    method = "Paiement Normal"
    if hasattr(order, 'payment_set') and order.payment_set.exists():
        payment = order.payment_set.first()
        method = payment.get_payment_method_display() if hasattr(payment, 'get_payment_method_display') else payment.payment_method
    p.drawString(1.5*cm, height-19.5*cm, f"Méthode: {method}")
    p.drawString(1.5*cm, height-20*cm, f"Date: {order.created_at.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(1.5*cm, height-20.5*cm, f"Statut: Payé")
    
    # Notes et conditions
    p.setFont("Helvetica-Bold", 10)
    p.drawString(1.5*cm, height-22*cm, "Notes et conditions:")
    p.setFont("Helvetica", 8)
    p.drawString(1.5*cm, height-22.7*cm, "• Cette facture est une preuve de paiement et doit être conservée pour référence future")
    p.drawString(1.5*cm, height-23.2*cm, "• Pour toute assistance, veuillez contacter notre service client au +237 672-456-789")
    p.drawString(1.5*cm, height-23.7*cm, "• Les retours sont acceptés dans un délai de 7 jours suivant la livraison")
    
    # Pied de page
    p.setStrokeColor(orange_color)
    p.setLineWidth(5)
    p.line(1*cm, 1*cm, width-1*cm, 1*cm)
    
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 0.7*cm, "KmerFusion SARL - RCCM 12345-CAM-2023 - Yaoundé, Cameroun")
    p.drawCentredString(width/2, 0.4*cm, "www.kmerfusion.com - support@kmerfusion.com - +237 672-456-789")
    
    # Réference de facturation unique
    p.rotate(90)
    p.setFillColor(colors.lightgrey)
    p.setFont("Helvetica", 6)
    p.drawString(2*cm, -width+0.5*cm, f"REF: {order.id}-{order.created_at.strftime('%Y%m%d%H%M%S')}")
    p.rotate(-90)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{order.id}.pdf"'
    
    return response




def payment_cancelled(request):
    return render(request, 'payment/cancelled.html')




def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Récupérer les données du formulaire
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Préparer le message
            email_message = f"""
            Nouveau message de : {name}
            Email : {email}
            
            {message}
            """
            
            # Envoyer l'email
            try:
                send_mail(
                    subject=f"Contact AgriConnect: {subject}",
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, "Votre message a été envoyé avec succès !")
                return redirect('contact')
            except Exception as e:
                messages.error(request, "Une erreur s'est produite lors de l'envoi du message. Veuillez réessayer.")
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})




@login_required(login_url='/login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Vérifier si l'utilisateur a déjà un panier
    cart, created = Cart.objects.get_or_create(
        user=request.user,
        ordered=False
    )
    
    # Vérifier si ce produit est déjà dans le panier
    cart_item, created = CartItem.objects.get_or_create(
        product=product,
        user=request.user,
        ordered=False
    )
    
    if created:
        cart_item.quantity = quantity
        cart_item.save()
        cart.items.add(cart_item)
        cart.save()
    else:
        # Si le produit est déjà dans le panier, augmenter la quantité
        cart_item.quantity += quantity
        cart_item.save()
    
    # Rediriger vers la page précédente ou vers le panier
    next_url = request.POST.get('next', 'cart')
    messages.success(request, f"{product.name} a été ajouté à votre panier.")
    return redirect(next_url)

@login_required(login_url='/login')
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user, ordered=False)
    cart_item.delete()
    messages.info(request, "Produit retiré du panier.")
    return redirect('cart')

@login_required(login_url='/login')
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user, ordered=False)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
        
    return redirect('cart')

@login_required(login_url='/login')
def cart_view(request):
    # Récupérer le panier de l'utilisateur
    try:
        cart = Cart.objects.get(user=request.user, ordered=False)
        cart_items = cart.items.all()
        total = sum(item.product.price * item.quantity for item in cart_items)
    except Cart.DoesNotExist:
        cart_items = []
        total = 0
    
    context = {
        'cart_items': cart_items,
        'total': total
    }
    
    return render(request, 'cart.html', context)

def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user, ordered=False)
        cart_items = cart.items.all()
        
        if not cart_items.exists():
            messages.warning(request, "Votre panier est vide.")
            return redirect('cart')
            
        total = sum(item.product.price * item.quantity for item in cart_items)
    except Cart.DoesNotExist:
        messages.warning(request, "Vous n'avez pas de panier actif.")
        return redirect('catalogue')
    
    context = {
        'cart_items': cart_items,
        'total': total
    }
    
    return render(request, 'checkout.html', context)
