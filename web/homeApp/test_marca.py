from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse


class MarcaVigiaTests(TestCase):
    """RF-015-06: the portal shows the VIGIA brand instead of the base logo."""

    def assertMarca(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "img/vigia.svg")
        self.assertNotContains(response, "img/logo.svg")

    def test_paginas_publicas(self):
        self.assertMarca(self.client.get(reverse("account_login")))
        catalogo = self.client.get(reverse("PlanesApp:catalogo"))
        self.assertMarca(catalogo)
        self.assertContains(catalogo, "VIGIA · Planes")

    def test_portal(self):
        user = User.objects.create_user(username="marca_sintetica", is_superuser=True)
        self.client.force_login(user)
        portal = self.client.get(reverse("Home"))
        self.assertMarca(portal)
        self.assertContains(portal, "· VIGIA</title>", html=False)

    @override_settings(ROOT_URLCONF="core.mobile_demo_urls")
    def test_descarga_de_la_demo(self):
        self.assertMarca(self.client.get("/descargar/"))
