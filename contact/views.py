import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import ContactForm
from .tasks import send_confirmation_email

# dummy webpage
def home(request):
    return render(request, "index.html")

# Contact form view
def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Extract cleaned data
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            message = form.cleaned_data["message"]

            # Prepare Autosend API payload
            payload = {
                "to": {
                    "email": settings.CONTACT_RECIPIENT_EMAIL,  # e.g., your personal email
                    "name": settings.CONTACT_RECIPIENT_NAME,
                },
                "from": {
                    "email": settings.FROM_EMAIL, # autosend registered email 
                    "name": settings.FROM_NAME,
                },
                "subject": f"New Contact Form Submission from {name}",
                "html": f"""
                <h2>New Message from {name}</h2>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Message:</strong></p>
                <p>{message}</p>
                """,
                "text": f"New Message from {name}\n\nEmail: {email}\n\nMessage:\n{message}",
                "replyTo": {"email": email, "name": name},
            }

            # Send via Autosend API
            headers = {
                "Authorization": f"Bearer {settings.AUTOSEND_API_KEY}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                settings.AUTOSEND_API_URL, json=payload, headers=headers
            )

            if response.status_code == 200:  # Accepted for delivery
                messages.success(request, "Your message has been sent successfully!")
                send_confirmation_email.delay(name,email,settings.FROM_NAME,settings.FROM_EMAIL,message);
                form = ContactForm()  # Reset the form
                return redirect("contact")
            else:
                messages.error(
                    request,
                    "Sorry, there was an issue sending your message. Please try again.",
                )
                # Log the error: print(response.json()) for debugging
                print(f"Error sending email: {response.status_code} - {response.text}")
                print("Autosend API Error:", response.json())
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()

    return render(request, "contactform.html", {"form": form})
