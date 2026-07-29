from rest_framework.renderers import JSONRenderer
class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response=(renderer_context or {}).get("response"); status=getattr(response,"status_code",200)
        if data is None or (isinstance(data,dict) and set(data)>={"success","message","data","errors"}): payload=data
        elif status>=400: payload={"success":False,"message":data.get("detail","Request failed.") if isinstance(data,dict) else "Request failed.","data":None,"errors":data}
        else: payload={"success":True,"message":"Request completed successfully.","data":data,"errors":None}
        return super().render(payload,accepted_media_type,renderer_context)
