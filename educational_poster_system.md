# School Educational Poster Classification & Tracking System

This document outlines a standardized physical classification system modeled after the Dewey Decimal system, combined with a Django database schema and Python/Pillow workflow to digitally catalog and track school educational posters.

---

## 1. The Educational Poster Decimal System (EPDS)

The physical storage is divided into 10 major numerical classes (000–900). Each poster receives a unique identifier matching its **Class . Subclass / Unique ID** (e.g., `500.2/014` for a Solar System poster).

### 000 – Classroom Management & Operations
*   010 Daily Routines, Calendars & Schedules
*   020 Rules, Behavior Expectations & Jobs
*   030 Grading Rubrics & Goal Trackers
*   040 Sign-out Sheets & Safety Protocols

### 100 – Social-Emotional Learning & Affirmations
*   110 Growth Mindset & Motivation
*   120 Emotional Regulation & Feelings Charts
*   130 Diversity, Inclusion & Community
*   140 Anti-Bullying & Kindness

### 200 – Language Arts & Literacy (Primary)
*   210 Alphabet & Phonics
*   220 Sight Words & Vocabulary
*   230 Parts of Speech & Grammar
*   240 Reading Strategies & Comprehension

### 300 – Literature & Language Arts (Advanced)
*   310 Literary Genres & Story Elements
*   320 Essay Writing & Rhetoric
*   330 Punctuation & Style Rules
*   340 Foreign Language Aids

### 400 – Mathematics (Foundational)
*   410 Numbers & Counting (0-100)
*   420 Addition & Subtraction
*   430 Multiplication & Division
*   440 Fractions, Decimals & Percentages

### 500 – Mathematics (Advanced & Applied)
*   510 Algebra & Formulas
*   520 Geometry & Shapes
*   530 Measurement, Time & Money
*   540 Data, Graphing & Statistics

### 600 – Natural Sciences
*   610 Life Cycles, Biology & Anatomy
*   620 Earth Science & Weather
*   630 Space & Astronomy
*   640 Physics & Chemistry Basics

### 700 – Social Studies & History
*   710 World Geography & Maps
*   720 National/State Geography & Civics
*   730 Historical Timelines
*   740 Biography & Key Figures

### 800 – Creative Arts & Technology
*   810 Color Wheels & Art Techniques
*   820 Music Theory & Instruments
*   830 Computer Science & Coding Basics
*   840 Maker Space & Engineering

### 900 – Seasonal & Rotating Displays
*   910 Autumn / Back to School
*   920 Winter Holidays
*   930 Spring / End of Year
*   940 Heritage Months & Cultural Days

---

## 2. Django Model Schema (`models.py`)

```python
from django.db import models
from django.core.validators import RegexValidator


class Poster(models.Model):
    title = models.CharField(
        max_length=255, help_text="Title printed on or describing the poster"
    )

    # Custom alphanumeric system validator matching: 000.0/000
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
    drawer_or_slot = models.CharField(max_length=50, blank=True, null=True)

    # Metadata
    grade_min = models.IntegerField(
        default=0, help_text="Minimum target grade (0 for K)"
    )
    grade_max = models.IntegerField(default=12, help_text="Maximum target grade")
    dimensions_inches = models.CharField(max_length=20, placeholder="18x24", blank=True)
    is_laminated = models.BooleanField(default=False)

    # Media & Tracking
    thumbnail = models.ImageField(
        upload_url="posters/thumbnails/", blank=True, null=True
    )
    date_added = models.DateField(auto_now_add=True)
    last_displayed = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"[{self.epds_code}] {self.title}"

    class Meta:
        ordering = ["epds_code"]
```

---

## 3. Pillow Image Processing Script (`utils.py`)

Automate thumbnail generation and watermark or overlay the physical barcode/EPDS identifier cleanly onto your digital preview image.

```python
from PIL import Image, ImageDraw, ImageFont
import os


def process_poster_image(
    input_image_path, epds_code, output_dir="media/posters/thumbnails/"
):
    """
    Resizes an uploaded poster photo into a uniform thumbnail
    and burns the physical EPDS location code into a clear lower banner.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with Image.open(input_image_path) as img:
        # 1. Maintain aspect ratio for a maximum bounding box of 400x400
        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        width, height = img.size

        # 2. Append a clean 40px high black label band at the bottom
        banner_height = 40
        new_height = height + banner_height

        # Create canvas background
        labeled_img = Image.new("RGB", (width, new_height), "black")
        # Paste original resized image onto it
        labeled_img.paste(img, (0, 0))

        # 3. Draw text using ImageDraw
        draw = ImageDraw.Draw(labeled_img)

        # Use default font or attempt to load a system TrueType font
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        text = f"LOC: {epds_code}"

        # Center the text box in the banner widthwise
        text_w = (
            draw.textlength(text, font=font) if hasattr(draw, "textlength") else 100
        )
        text_x = max((width - text_w) // 2, 10)
        text_y = height + ((banner_height - 20) // 2)

        # Render text in crisp white
        draw.text((text_x, text_y), text, fill="white", font=font)

        # 4. Save to destination
        filename = f"{epds_code.replace('.', '_').replace('/', '_')}.jpg"
        save_path = os.path.join(output_dir, filename)
        labeled_img.save(save_path, "JPEG", quality=85)

        return save_path
```
