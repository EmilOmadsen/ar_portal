# 📝 CONTRACT TEMPLATE PLACEHOLDERS

**Complete reference for Word template (.docx) development**

Backend provides **ONLY data** — Word handles **ALL formatting, loops, and conditionals**.

---

## ✅ **1. PROJECT IDENTIFICATION**

```jinja2
{{project_code}}        → "SUN2025-R-042" (auto-formatted with zero-padding)
{{project_number}}      → "42" (raw number)
{{year}}                → 2025
```

**Example usage in Word:**
```
Contract Number: {{project_code}}
```

---

## ✅ **2. ARTISTS (LOOP)**

### Artist Object Fields:
```jinja2
{{artist.stage_name}}   → "DJ Example"
{{artist.full_name}}    → "John Example Smith"
{{artist.address}}      → "Main Street 123"
{{artist.postcode}}     → "1234"
{{artist.city}}         → "Copenhagen"
{{artist.country}}      → "Denmark"
{{artist.email}}        → "artist@example.com"
{{artist.ipi}}          → "123456789"
{{artist.id_number}}    → "123456-7890"
```

### Loop Structure (for multiple artists):

**Recording signature** (uses stage name):
```jinja2
{% for artist in artists %}
Artist: {{artist.stage_name}}
Address: {{artist.address}}, {{artist.postcode}} {{artist.city}}, {{artist.country}}
Email: {{artist.email}}
{% if not loop.first %}, {% endif %}
{% endfor %}
```

**Publishing signature** (uses full name):
```jinja2
{% for artist in artists %}
Writer Name: {{artist.full_name}}
IPI: {{artist.ipi}}
{% endfor %}
```

**Multiple artists in text** (e.g., "DJ Test and DJ Test2"):
```jinja2
{{artists[0].stage_name}}{% for artist in artists[1:] %} and {{artist.stage_name}}{% endfor %}
```

---

## ✅ **3. ROYALTIES**

```jinja2
{{royalty_percent}}     → 50 (recording royalty percentage)
{{writer_share}}        → 50 (publishing - writer share, always 50)
{{publisher_share}}     → 50 (publishing - publisher share, always 50)
```

**Example usage:**
```
Artist shall receive {{royalty_percent}}% of net receipts...
Writer: {{writer_share}}%
Publisher: {{publisher_share}}%
```

---

## ✅ **4. PUBLISHING TOGGLE**

```jinja2
{{publishing_included}} → True/False
```

**Usage in Word:**
```jinja2
{% if publishing_included %}
  ... entire publishing addendum section ...
{% endif %}
```

---

## ✅ **5. MARKETING RECOUPMENT**

### Fields:
```jinja2
{{marketing_recoupment_enabled}}           → True/False
{{marketing_recoupment_amount_numeric}}    → 5000
{{marketing_recoupment_amount_words}}      → "Five Thousand"
```

### Optional Additional Amount:
```jinja2
{{marketing_option_enabled}}               → True/False
{{marketing_option_amount_numeric}}        → 10000
{{marketing_option_amount_words}}          → "Ten Thousand"
```

### Word Template Structure:
```jinja2
{% if marketing_recoupment_enabled %}
Company shall be allowed to offset a recoupable cost of 
USD {{marketing_recoupment_amount_numeric}} 
({{marketing_recoupment_amount_words}} American Dollars)
{% if marketing_option_enabled %}
with an option of USD {{marketing_option_amount_numeric}} 
({{marketing_option_amount_words}} American Dollars)
{% endif %}
, all from royalties due to Artist for each Recording...
{% endif %}
```

---

## ✅ **6. STANDARD ADVANCE**

### Fields:
```jinja2
{{advance_enabled}}            → True/False
{{advance_amount_numeric}}     → 15000
{{advance_amount_words}}       → "Fifteen Thousand"
```

### Word Template:
```jinja2
{% if advance_enabled %}
Company agrees to pay Artist an advance of 
USD {{advance_amount_numeric}} 
({{advance_amount_words}} American Dollars)
{% endif %}
```

---

## ✅ **7. MILESTONE ADVANCE** (NEW!)

### Fields:
```jinja2
{{milestone_enabled}}                      → True/False
{{milestone_daily_streams}}                → 50000
{{milestone_period_days}}                  → 30
{{milestone_advance_amount_numeric}}       → 25000
{{milestone_advance_amount_words}}         → "Twenty Five Thousand"
```

### Word Template:
```jinja2
{% if milestone_enabled %}
If the Recording achieves {{milestone_daily_streams}} daily streams 
for {{milestone_period_days}} consecutive days, 
Company agrees to pay an additional advance of 
USD {{milestone_advance_amount_numeric}} 
({{milestone_advance_amount_words}} American Dollars)
{% endif %}
```

---

## 📋 **COMPLETE CONTEXT STRUCTURE**

Backend sends this dictionary to Word:

```python
{
  # Project
  "project_code": "SUN2025-R-042",
  "project_number": "42",
  "year": 2025,
  
  # Artists (list)
  "artists": [
    {
      "stage_name": "...",
      "full_name": "...",
      "address": "...",
      "postcode": "...",
      "city": "...",
      "country": "...",
      "email": "...",
      "ipi": "...",
      "id_number": "..."
    }
  ],
  
  # Royalties
  "royalty_percent": 50,
  "writer_share": 50,
  "publisher_share": 50,
  
  # Publishing toggle
  "publishing_included": True/False,
  
  # Marketing recoupment
  "marketing_recoupment_enabled": True/False,
  "marketing_recoupment_amount_numeric": 5000,
  "marketing_recoupment_amount_words": "Five Thousand",
  "marketing_option_enabled": True/False,
  "marketing_option_amount_numeric": 10000,
  "marketing_option_amount_words": "Ten Thousand",
  
  # Standard advance
  "advance_enabled": True/False,
  "advance_amount_numeric": 15000,
  "advance_amount_words": "Fifteen Thousand",
  
  # Milestone advance
  "milestone_enabled": True/False,
  "milestone_daily_streams": 50000,
  "milestone_period_days": 30,
  "milestone_advance_amount_numeric": 25000,
  "milestone_advance_amount_words": "Twenty Five Thousand"
}
```

---

## 🎯 **GOLDEN RULES**

1. **Backend = Data Only** — Never generates text/clauses
2. **Word = All Text** — Handles formatting, loops, conditionals
3. **All Money = Numeric + Words** — Always both formats
4. **Booleans = Visibility** — True = show section, False = hide
5. **Arrays = Word Loops** — Backend sends raw list, Word iterates

---

## 🔧 **UPDATING THE WORD TEMPLATE**

Use **LibreOffice Writer** (free) to edit the .docx file with these placeholders.

**Microsoft Word without subscription may corrupt Jinja2 tags!**

Download LibreOffice: https://www.libreoffice.org/download/

---

**Last Updated:** January 2026  
**Spec Version:** CONTRACT LOGIC v1.0
