from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from rest_framework import permissions,status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from audit_logs.utils import audit
from common.permissions import IsAdministratorResponder
from .models import User
from .serializers import *
class VerifiedTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self,attrs):
        token=RefreshToken(attrs["refresh"])
        try: user=User.objects.get(pk=token["user_id"])
        except User.DoesNotExist: from rest_framework.exceptions import AuthenticationFailed; raise AuthenticationFailed("Account not found.")
        if not user.is_active or not user.is_verified:
            from rest_framework.exceptions import PermissionDenied; raise PermissionDenied("Account is inactive or unverified.")
        return super().validate(attrs)
class VerifiedTokenRefreshView(TokenRefreshView): serializer_class=VerifiedTokenRefreshSerializer
class LoginView(GenericAPIView):
    serializer_class=LoginSerializer
    permission_classes=[permissions.AllowAny]; authentication_classes=[]
    def post(self,request):
        s=LoginSerializer(data=request.data)
        if not s.is_valid(): audit(request,"failed_login","accounts",new={"email":request.data.get("email","")}); return Response(s.errors,status=400)
        user=s.validated_data["user"]; refresh=RefreshToken.for_user(user); audit(request,"login","accounts",user)
        return Response({"access":str(refresh.access_token),"refresh":str(refresh),"user":UserSerializer(user,context={"request":request}).data})
class LogoutView(GenericAPIView):
    serializer_class=LogoutSerializer
    def post(self,request):
        try: RefreshToken(request.data["refresh"]).blacklist()
        except Exception: return Response({"refresh":["Invalid or expired refresh token."]},status=400)
        audit(request,"logout","accounts",request.user); return Response(status=204)
class ProfileView(GenericAPIView):
    serializer_class=UserSerializer
    def get(self,r): return Response(UserSerializer(r.user,context={"request":r}).data)
    def patch(self,r):
        s=UserSerializer(r.user,data=r.data,partial=True,context={"request":r}); s.is_valid(raise_exception=True); s.save(); audit(r,"update","accounts",r.user); return Response(s.data)
class ChangePasswordView(GenericAPIView):
    serializer_class=ChangePasswordSerializer
    def post(self,r):
        s=ChangePasswordSerializer(data=r.data); s.is_valid(raise_exception=True)
        if not r.user.check_password(s.validated_data["old_password"]): return Response({"old_password":["Incorrect password."]},status=400)
        r.user.set_password(s.validated_data["new_password"]); r.user.save(); audit(r,"change_password","accounts",r.user); return Response({"detail":"Password changed."})
class ForgotPasswordView(GenericAPIView):
    serializer_class=ForgotPasswordSerializer
    permission_classes=[permissions.AllowAny]; authentication_classes=[]
    def post(self,r):
        s=ForgotPasswordSerializer(data=r.data); s.is_valid(raise_exception=True); user=User.objects.filter(email=s.validated_data["email"].lower(),is_active=True).first()
        if user:
            uid=urlsafe_base64_encode(force_bytes(user.pk)); token=default_token_generator.make_token(user); url=f"{settings.FRONTEND_RESET_URL}?uid={uid}&token={token}"
            send_mail("Hazard Hero password reset",f"Reset your password: {url}",settings.DEFAULT_FROM_EMAIL,[user.email])
        return Response({"detail":"If the account exists, reset instructions were sent."})
class ResetPasswordView(GenericAPIView):
    serializer_class=ResetPasswordSerializer
    permission_classes=[permissions.AllowAny]; authentication_classes=[]
    def post(self,r):
        s=ResetPasswordSerializer(data=r.data); s.is_valid(raise_exception=True)
        try: user=User.objects.get(pk=force_str(urlsafe_base64_decode(s.validated_data["uid"])))
        except Exception: return Response({"token":["Invalid reset link."]},status=400)
        if not default_token_generator.check_token(user,s.validated_data["token"]): return Response({"token":["Invalid or expired reset link."]},status=400)
        user.set_password(s.validated_data["new_password"]); user.save(); return Response({"detail":"Password reset successful."})
class UserViewSet(viewsets.ModelViewSet):
    queryset=User.objects.order_by("last_name","first_name"); serializer_class=UserSerializer; permission_classes=[IsAdministratorResponder]; filterset_fields=["is_active","is_verified"]; search_fields=["email","first_name","last_name","office","position"]; ordering_fields=["email","first_name","last_name","created_at"]
    def perform_create(self,s): obj=s.save(); audit(self.request,"account_creation","accounts",obj,new=s.data)
    def destroy(self,r,*a,**k): return Response({"detail":"Use deactivate; accounts are retained for audit integrity."},status=405)
    @action(detail=True,methods=["post"])
    def activate(self,r,pk=None): obj=self.get_object(); obj.is_active=True; obj.save(); audit(r,"account_activation","accounts",obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["post"])
    def deactivate(self,r,pk=None):
        obj=self.get_object()
        if obj==r.user: return Response({"detail":"You cannot deactivate your own account."},status=400)
        obj.is_active=False; obj.save(); audit(r,"account_deactivation","accounts",obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["post"])
    def verify(self,r,pk=None): obj=self.get_object(); obj.is_verified=True; obj.save(); audit(r,"verify","accounts",obj); return Response(self.get_serializer(obj).data)
