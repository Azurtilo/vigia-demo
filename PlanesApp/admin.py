from django import forms
from django.contrib import admin

from .models import Plan, PlanBenefit


class BenefitInline(admin.TabularInline):
    model = PlanBenefit
    extra = 0


class PlanAdminForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = "__all__"

    def clean(self):
        data = super().clean()
        amount = data.get("amount_clp")
        if self.instance.code == "free":
            if amount != 0:
                self.add_error("amount_clp", "Free debe conservar su valor cero.")
            if data.get("active") is False:
                self.add_error(
                    "active", "Free debe estar disponible para el registro público."
                )
        elif amount == 0:
            self.add_error(
                "amount_clp", "Un plan pagado debe tener un valor mayor que cero."
            )
        return data


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    form = PlanAdminForm
    list_display = ["name", "amount_clp", "active", "display_order"]
    readonly_fields = ["code", "currency", "updated_at"]
    inlines = [BenefitInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
