from rest_framework.exceptions import ValidationError
from .models import Language,SUPPORTED_CODES
def requested_language(request):
    code=request.query_params.get("language","en").lower()
    if code not in SUPPORTED_CODES: raise ValidationError({"language":["Supported codes are en, fil, and ceb."]})
    if not Language.objects.filter(language_code=code,is_active=True).exists(): raise ValidationError({"language":["This language is currently inactive."]})
    return code
def choose_translation(parent,related_name,code):
    qs=getattr(parent,related_name).filter(status="Published").select_related("language")
    requested=next((x for x in qs if x.language.language_code==code),None)
    english=next((x for x in qs if x.language.language_code=="en"),None)
    chosen=requested or english
    return chosen,(chosen.language.language_code if chosen else "en"),bool(code!="en" and (not requested))
def completion(parent,related_name):
    existing={x.language.language_code:x.status for x in getattr(parent,related_name).select_related("language")}
    return {code:existing.get(code,"Missing") for code in SUPPORTED_CODES}
def localized_values(parent,related_name,code,mapping):
    translation,returned,fallback=choose_translation(parent,related_name,code)
    values={output:(getattr(translation,translated) if translation else getattr(parent,original)) for output,(translated,original) in mapping.items()}
    return {"requested_language":code,"returned_language":returned,"used_fallback":fallback,**values},translation
