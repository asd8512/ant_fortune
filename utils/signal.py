from django.dispatch import Signal

pre_soft_delete = Signal(providing_args=["instance", "kwargs"])
