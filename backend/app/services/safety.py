import re
from collections import Counter
from ..schemas import Analysis

def norm(value): return ' '.join((value or '').split()).casefold()

def category_for(item):
    if item.kind == 'medicine': return 'medicine'
    if item.kind == 'follow_up': return 'follow_up'
    if item.kind == 'warning': return 'warning'
    source = norm(item.source + ' ' + item.wording)
    if re.search(r'\b(diet|food|eat|drink|salt|fluid|water|meal|आहार|खाणे|पाणी|जेवण|आहाराचे)\b', source): return 'diet'
    if re.search(r'\b(walk|walking|exercise|activity|lifting|lift|stairs|rest|bed rest|चालणे|व्यायाम|विश्रांती|उचलणे)\b', source): return 'activity'
    if re.search(r'\b(precaution|avoid|keep|clean|dry|wound|dressing|काळजी|टाळा|स्वच्छ|जपणे)\b', source): return 'precaution'
    return 'other'

def validate_grounding(result: Analysis, text: str) -> Analysis:
    ids = [item.id for item in result.items]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate item IDs')
    source_text = norm(text)
    medicine_counts = Counter(norm(i.title) for i in result.items if i.kind == 'medicine')
    for item in result.items:
        item.category = category_for(item)
        concerns = list(item.concerns)
        evidence = norm(item.source)
        if not evidence or evidence not in source_text:
            concerns.append('Source evidence could not be matched to the document.')
        # Actionable fields must be literal excerpts, not generated paraphrases.
        for name in ('wording', 'dosage', 'frequency', 'duration', 'timing', 'date'):
            value = getattr(item, name)
            if value and norm(value) not in evidence:
                concerns.append(f'{name.capitalize()} is not supported by the source excerpt.')
        if item.kind == 'medicine':
            if norm(item.title) not in evidence: concerns.append('Medicine name does not match the source.')
            if not all((item.dosage, item.frequency, item.duration)):
                concerns.append('Dose, frequency or duration is missing. Ask a healthcare professional.')
            if medicine_counts[norm(item.title)] > 1:
                concerns.append('Multiple entries for this medicine require professional clarification.')
            if re.search(r'\?|unclear|illegible|conflict', item.source, re.I):
                concerns.append('The original medicine instructions are ambiguous.')
        item.concerns = list(dict.fromkeys(concerns))
        item.uncertain = item.uncertain or bool(concerns)
    return result

def apply_processing_safety(result, info):
    warnings = list(info.warnings)
    warnings.extend('Unreadable region: ' + region for region in info.unreadable_regions)
    if info.document_mode == 'handwritten':
        warnings.append('Handwritten medication details need professional verification; patient review cannot authorize a medicine reminder.')
    result.uncertainties = list(dict.fromkeys(result.uncertainties + warnings))
    for item in result.items:
        if (info.document_mode == 'handwritten' and item.kind == 'medicine') or info.warnings or info.unreadable_regions:
            item.uncertain = True
            item.professional_verification_required = True
            reason = 'Needs Professional Verification: compare the original image with a healthcare professional.'
            if reason not in item.concerns:
                item.concerns.append(reason)
    return result
