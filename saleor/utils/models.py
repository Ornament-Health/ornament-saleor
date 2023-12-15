from django.db import models
from django.db.models.fields import DateField, DateTimeField, TimeField


class AutoNowUpdateFieldsMixin(models.Model):
    # fixes wontfix issue https://code.djangoproject.com/ticket/22981

    auto_now_update_fields = None

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields:
            auto_now_update_fields = [
                i.name
                for i in self._meta.fields
                if isinstance(i, (DateField, DateTimeField, TimeField))
                and i.auto_now
                and (
                    not self.auto_now_update_fields
                    or i.name in self.auto_now_update_fields
                )
            ]
            if auto_now_update_fields:
                kwargs["update_fields"] = list(
                    {*update_fields, *auto_now_update_fields}
                )

        return super().save(*args, **kwargs)
