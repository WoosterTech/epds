from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, final, override

from django.core.validators import RegexValidator
from django.db import models

from .utils import process_poster_canvas

if TYPE_CHECKING:
    from collections.abc import Collection


@final
class Poster(models.Model):
    title = models.CharField(
        max_length=255, help_text="Title printed on or describing the poster"
    )

    epds_validator = RegexValidator(
        regex=r"^\d{3}\.\d{1}/\d{3}$",
        message="Format must be exactly XXX.X/XXX (e.g., 530.2/014)",
    )
    epds_code = models.CharField(
        max_length=11,
        validators=[epds_validator],
        unique=True,
        help_text="Educational Poster Decimal System physical locator identifier",
    )

    # Physical Storage Placement
    bin_number = models.CharField(
        max_length=50, help_text="Physical box, portfolio case, or bin name"
    )
    drawer_or_slot = models.CharField(max_length=50, blank=True, default="")

    # Metadata
    grade_min = models.IntegerField(
        default=0, help_text="Minimum target grade (0 for K)"
    )
    grade_max = models.IntegerField(default=12, help_text="Maximum target grade")

    dimensions_validator = RegexValidator(
        regex=r"^\d+(?:\.\d+)?[Xx]\d+(?:\.\d+)?$",
        message='Format must be two numbers with an "x" between them (e.g.,)',
    )
    dimensions_inches = models.CharField(
        max_length=20, validators=[dimensions_validator], blank=True
    )
    is_laminated = models.BooleanField(default=False)

    # Media & Tracking
    original_image = models.ImageField(upload_to="posters/originals/")
    thumbnail_image = models.ImageField(upload_to="posters/thumbnails", blank=True)
    date_added = models.DateField(auto_now_add=True)
    last_displayed = models.DateField(blank=True, null=True)

    if TYPE_CHECKING:
        pk: models.BigAutoField | None
        _loaded_values: dict[str, Any]  # pyright: ignore[reportExplicitAny, reportUninitializedInstanceVariable]

    @final
    class Meta:
        ordering = ("epds_code",)

    @override
    def __str__(self):
        return f"[{self.epds_code}] {self.title}"

    @override
    def save(self, *args: Any, **kwargs: Any):  # pyright: ignore[reportAny, reportExplicitAny]
        # 1. save the initial record first so we have an ID and a file path
        is_new = self._state.adding
        super().save(*args, **kwargs)  # pyright: ignore[reportAny]

        # 2. trigger the decoupled utility if a new image was provided
        loaded_values = self._loaded_values
        if (
            is_new or (self.original_image != loaded_values["original_image"])
        ) and self.original_image:
            relative_thumb_path = process_poster_canvas(
                input_file_path=Path(self.original_image.path), epds_code=self.epds_code
            )
            _ = Poster.objects.filter(pk=self.pk).update(
                thumbnail_image=str(relative_thumb_path)
            )

    @override
    @classmethod
    def from_db(
        cls,
        db: str | None,
        field_names: Collection[str],
        values: Collection[Any],  # pyright: ignore[reportExplicitAny]
    ) -> Self:
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(zip(field_names, values, strict=False))  # noqa: SLF001

        return instance
