from PlanesApp.permissions import ClientMixin


class CareOwnerMixin(ClientMixin):
    """Every active account cares for its own patients, without a root exception."""
