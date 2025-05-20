from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import render

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False

    def add_message(self, request, level, message_template, message_context=None, extra_tags=''):
        # Skip the login success message
        if message_template == "account/messages/logged_in.txt":
            return
        super().add_message(request, level, message_template, message_context, extra_tags)

ALLOWED_EMAILS = {
    "holdjt912@gmail.com",
    # etc...
}

class WhitelistSocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Show extra_data or do your manual email assignment...
        user = sociallogin.user
        if not user.email and "email" in sociallogin.account.extra_data:
            user.email = sociallogin.account.extra_data["email"].lower().strip()

        email = user.email or ''
        #print("DEBUG => social login email:", email)

        if email not in ALLOWED_EMAILS:
            # Instead of raising PermissionDenied, serve a custom response:
            response = render(request, "account/email_not_allowed.html", {
                "message": "Sorry, your email is not allowed at this time."
            })
            raise ImmediateHttpResponse(response)
