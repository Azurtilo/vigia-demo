"""allauth password forms with the live checklist (spec 018)."""

from allauth.account import forms as allauth_forms

from .password_rules import PasswordRulesMixin


class ChangePasswordForm(PasswordRulesMixin, allauth_forms.ChangePasswordForm):
    personal_fields = ()


class SetPasswordForm(PasswordRulesMixin, allauth_forms.SetPasswordForm):
    personal_fields = ()


class ResetPasswordKeyForm(PasswordRulesMixin, allauth_forms.ResetPasswordKeyForm):
    personal_fields = ()
