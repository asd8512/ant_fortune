from django.db import models
from django.db import transaction
from django.db.models import ProtectedError
from django.db.models import Manager

from utils.signal import pre_soft_delete


class SoftDeleteQuerySet(models.query.QuerySet):

    def soft_delete(self, batch_delete=False):
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
        query = self._chain()
        count = query.count()
        if count == 0:
            return False, 0
        if batch_delete:
            query.update(is_deleted=True)
        else:
            # 逐一软删除，触发pre_save信号
            with transaction.atomic():
                for item in query:
                    item.soft_delete()
        return True, count


class SoftDeleteManager(models.Manager):
    """ Use this manager to get objects that have a is_deleted field """

    use_for_related_fields = True

    def get_queryset(self):
        return super(SoftDeleteManager, self).get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        return super(SoftDeleteManager, self).get_queryset()

    def deleted_set(self):
        return super(SoftDeleteManager, self).get_queryset().filter(is_deleted=True)

    def restore(self, pk):
        return self.all_with_deleted().filter(pk=pk).update(is_deleted=False)


class SoftDeleteMixin(object):
    """works with models.Model"""

    def soft_delete(self):
        assert self.pk is not None, (
                "%s object can't be deleted because its %s attribute is set to None."
                % (self._meta.object_name, self._meta.pk.attname)
        )
        assert getattr(self, "is_deleted", None) is not None, (
            f"{self._meta.object_name}"
            f"is_deleted attribute is None, "
            f"cannot soft delete"
        )
        pre_soft_delete.send(sender=self.__class__, instance=self)
        self.is_deleted = True
        self.save()
        self.on_delete()

    def on_delete(self):
        related_objects = self._meta.related_objects
        for related in related_objects:
            if related.on_delete in [None, models.DO_NOTHING]:
                continue
            cascade_type = related.on_delete.__name__
            related_column = related.field.column
            try:
                if related.related_name is not None:
                    related_manager = getattr(self, related.related_name)
                else:
                    continue
            except related.related_model.DoesNotExist:
                continue
            if isinstance(related_manager, Manager):
                self.process_queryset(related_manager, cascade_type, related_column)
            else:
                obj = related_manager
                self.process_obj(obj, cascade_type, related_column)

    def process_queryset(self, related_manager, cascade_type, related_column):
        data = {related_column: None}
        queryset = related_manager.all()
        if cascade_type == "SET_NULL":
            related_manager.update(**data)
        elif cascade_type == "CASCADE":
            if isinstance(queryset, SoftDeleteQuerySet):
                queryset.soft_delete()
            else:
                queryset.delete()
        elif cascade_type == "PROTECT":
            if queryset.count() > 0:
                raise ProtectedError("", related_column)
        else:
            raise NotImplementedError()

    def process_obj(self, obj, cascade_type, related_column):
        if cascade_type == "SET_NULL":
            setattr(obj, related_column, None)
            obj.save()
        elif cascade_type == "CASCADE":
            if hasattr(obj, "soft_delete"):
                obj.soft_delete()
            else:
                obj.delete()
        elif cascade_type == "PROTECT":
            raise ProtectedError("", related_column)
        else:
            raise NotImplementedError()
