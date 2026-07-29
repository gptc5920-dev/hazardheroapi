from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase,TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import User
from alerts.models import EmergencyAlert
from audit_logs.models import AuditLog
from emergency_contacts.models import EmergencyContact
from evacuation_centers.models import EvacuationCenter
from go_bag.models import GoBagItem
from guidelines.models import Guideline
from guidelines.models import GuidelineTranslation,GuidelineMedia,GuidelineMediaTranslation
from languages.models import Language
from config.settings import normalize_deployment_host,normalize_deployment_origin


class DeploymentSettingsTests(SimpleTestCase):
    def test_coolify_hostname_normalization(self):
        self.assertEqual(
            normalize_deployment_host("http://api.example.com:8000/path"),
            "api.example.com",
        )
        self.assertEqual(
            normalize_deployment_host("api.example.com:8000"),
            "api.example.com",
        )

    def test_coolify_origin_normalization(self):
        self.assertEqual(
            normalize_deployment_origin("https://api.example.com:8443/path"),
            "https://api.example.com:8443",
        )
        self.assertIsNone(normalize_deployment_origin("api.example.com"))

class HazardHeroAPITests(TestCase):
    def setUp(self):
        self.client=APIClient(); self.user=User.objects.create_user(email="responder@example.com",password="StrongPass123!",first_name="Ada",last_name="Reyes",is_active=True,is_verified=True)
        login=self.client.post("/api/responder/auth/login/",{"email":self.user.email,"password":"StrongPass123!"},format="json"); self.assertEqual(login.status_code,200); self.access=login.data["access"]; self.refresh=login.data["refresh"]
        self.item=GoBagItem.objects.create(name="Drinking Water",description="Three-day supply",category="Food and Water",quantity=3,unit="liters",priority_level="Critical",is_required=True,is_active=True)
        self.guideline=Guideline.objects.create(title="Flood Safety",summary="Stay safe",content="Move to high ground.",category="During an Emergency",emergency_type="Flood",status="Published",is_active=True,published_at=timezone.now())
        self.center=EvacuationCenter.objects.create(name="Central School",description="",center_code="EC-001",region="IX",province="Zamboanga del Norte",city_municipality="Dipolog",barangay="Central",street_address="Main Street",latitude="8.5000000",longitude="123.2800000",total_capacity=100,current_occupancy=20,contact_person="Officer",contact_number="09170000000",operating_status="Operational",availability_status="Available",facility_type="School",supported_emergency_types=["Flood"],is_active=True)
        self.contact=EmergencyContact.objects.create(organization_name="City Rescue",contact_type="Rescue Team",primary_phone_number="0917 111 2222",region="IX",province="Zamboanga del Norte",city_municipality="Dipolog",barangay="Central",availability="24/7",emergency_types=["Flood"],is_verified=True,is_active=True)
        self.alert=EmergencyAlert.objects.create(title="Flood Warning",message="Rising water",instructions="Evacuate now",alert_type="Flood",severity_level="Critical",status="Active",source="CDRRMO",region="IX",province="Zamboanga del Norte",city_municipality="Dipolog",barangay="Central",latitude="8.5020000",longitude="123.2820000",radius_km="20.00",affected_areas=["Central"],evacuation_required=True,recommended_evacuation_center=self.center,starts_at=timezone.now()-timedelta(hours=1),expires_at=timezone.now()+timedelta(hours=6),published_at=timezone.now(),is_public=True,is_active=True)
    def auth(self): self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")
    def test_health_check(self):
        response=self.client.get("/health/"); self.assertEqual(response.status_code,200); self.assertEqual(response.json(),{"status":"ok","database":"ok"})
    def test_all_citizen_modules_are_anonymous(self):
        for url in ["/api/citizen/go-bag/","/api/citizen/guidelines/","/api/citizen/evacuation-centers/","/api/citizen/emergency-contacts/","/api/citizen/alerts/"]:
            self.assertEqual(self.client.get(url).status_code,200,url)
    def test_citizen_mutations_rejected(self):
        for method in ["post","put","patch","delete"]: self.assertIn(getattr(self.client,method)("/api/citizen/go-bag/",{},format="json").status_code,[403,405])
    def test_public_exclusions(self):
        self.guideline.status="Draft"; self.guideline.save(); self.contact.is_verified=False; self.contact.save(); self.item.soft_delete(); self.alert.expires_at=timezone.now()-timedelta(minutes=1); EmergencyAlert.all_objects.filter(pk=self.alert.pk).update(expires_at=self.alert.expires_at)
        self.assertEqual(self.client.get("/api/citizen/guidelines/").data["count"],0); self.assertEqual(self.client.get("/api/citizen/emergency-contacts/").data["count"],0); self.assertEqual(self.client.get("/api/citizen/go-bag/").data["count"],0); self.assertEqual(self.client.get("/api/citizen/alerts/").data["count"],0)
    def test_nearby_endpoints(self):
        query={"latitude":8.5,"longitude":123.28,"radius":10}
        for url in ["/api/citizen/evacuation-centers/nearby/","/api/citizen/alerts/nearby/"]: self.assertEqual(len(self.client.get(url,query).data),1)
    def test_jwt_refresh_and_logout_blacklist(self):
        rotated=self.client.post("/api/responder/auth/refresh/",{"refresh":self.refresh},format="json"); self.assertEqual(rotated.status_code,200); current=rotated.data["refresh"]
        self.auth(); self.assertEqual(self.client.post("/api/responder/auth/logout/",{"refresh":current},format="json").status_code,204)
        self.assertEqual(self.client.post("/api/responder/auth/refresh/",{"refresh":current},format="json").status_code,401)
    def test_unverified_and_inactive_login_rejected(self):
        for field in ["is_verified","is_active"]:
            setattr(self.user,field,False); self.user.save(); response=self.client.post("/api/responder/auth/login/",{"email":self.user.email,"password":"StrongPass123!"},format="json"); self.assertEqual(response.status_code,400); setattr(self.user,field,True); self.user.save()
    def test_responder_go_bag_crud_soft_restore_permanent_delete(self):
        self.auth(); payload={"name":"First Aid Kit","description":"Medical kit","category":"Medical Supplies","quantity":1,"unit":"kit","priority_level":"High","is_required":True,"is_active":True,"display_order":1}
        created=self.client.post("/api/responder/go-bag/",payload,format="json"); self.assertEqual(created.status_code,201); pk=created.data["id"]
        self.assertEqual(self.client.patch(f"/api/responder/go-bag/{pk}/",{"quantity":2},format="json").status_code,200); self.assertEqual(self.client.delete(f"/api/responder/go-bag/{pk}/").status_code,204); self.assertEqual(self.client.post(f"/api/responder/go-bag/{pk}/restore/").status_code,200); self.client.delete(f"/api/responder/go-bag/{pk}/"); self.assertEqual(self.client.delete(f"/api/responder/go-bag/{pk}/permanent-delete/").status_code,204)
    def test_guideline_publish_and_archive(self):
        self.auth(); self.guideline.status="Draft"; self.guideline.save(); self.assertEqual(self.client.post(f"/api/responder/guidelines/{self.guideline.pk}/publish/").data["status"],"Published"); self.assertEqual(self.client.post(f"/api/responder/guidelines/{self.guideline.pk}/archive/").data["status"],"Archived")
    def test_capacity_calculation_and_validation(self):
        self.auth(); result=self.client.patch(f"/api/responder/evacuation-centers/{self.center.pk}/capacity/",{"current_occupancy":40},format="json"); self.assertEqual(result.data["available_slots"],60); self.assertEqual(self.client.patch(f"/api/responder/evacuation-centers/{self.center.pk}/capacity/",{"current_occupancy":101},format="json").status_code,400)
    def test_contact_verify_and_alert_transitions(self):
        self.auth(); self.contact.is_verified=False; self.contact.save(); self.assertTrue(self.client.post(f"/api/responder/emergency-contacts/{self.contact.pk}/verify/").data["is_verified"]); self.assertEqual(self.client.post(f"/api/responder/alerts/{self.alert.pk}/resolve/").data["status"],"Resolved")
    def test_alert_validation(self):
        self.auth(); data={"title":"Bad critical alert","message":"Danger","instructions":"","alert_type":"Flood","severity_level":"Critical","source":"Office","affected_areas":[],"evacuation_required":True,"starts_at":timezone.now(),"expires_at":timezone.now()-timedelta(hours=1)}; self.assertEqual(self.client.post("/api/responder/alerts/",data,format="json").status_code,400)
    def test_file_validation(self):
        self.auth(); bad=SimpleUploadedFile("payload.exe",b"MZbad",content_type="application/octet-stream"); response=self.client.patch(f"/api/responder/go-bag/{self.item.pk}/",{"image":bad},format="multipart"); self.assertEqual(response.status_code,400)
    def test_search_filter_and_audit(self):
        self.assertEqual(self.client.get("/api/citizen/go-bag/",{"search":"Drinking"}).data["count"],1); self.auth(); self.client.patch(f"/api/responder/go-bag/{self.item.pk}/",{"quantity":4},format="json"); self.assertTrue(AuditLog.objects.filter(action="update",module="go_bag").exists()); self.assertEqual(self.client.get("/api/responder/audit-logs/").status_code,200)
    def test_responder_requires_authentication(self): self.assertEqual(self.client.get("/api/responder/go-bag/").status_code,401)

    def _translation(self,code,status="Published",title=None):
        return GuidelineTranslation.objects.create(guideline=self.guideline,language=Language.objects.get(language_code=code),translated_title=title or f"{code} title",translated_summary=f"{code} summary",translated_content=f"{code} content",translated_safety_instructions=f"{code} safety",status=status)
    def test_exact_three_public_languages_available(self):
        response=self.client.get("/api/citizen/languages/"); self.assertEqual(response.status_code,200); self.assertEqual([x["language_code"] for x in response.data],["en","fil","ceb"]); self.assertTrue(response.data[0]["is_default"])
    def test_unsupported_language_and_additional_language_rejected(self):
        self.assertEqual(self.client.get("/api/citizen/guidelines/",{"language":"fr"}).status_code,400)
        with self.assertRaises(ValidationError): Language(name="French",native_name="Français",language_code="fr").save()
        self.auth(); self.assertEqual(self.client.post("/api/responder/languages/",{"language_code":"fr"},format="json").status_code,405)
    def test_english_cannot_be_deactivated_or_deleted(self):
        english=Language.objects.get(language_code="en"); self.auth(); self.assertEqual(self.client.patch(f"/api/responder/languages/{english.pk}/",{"is_active":False},format="json").status_code,400)
        english.is_active=False
        with self.assertRaises(ValidationError): english.save()
        with self.assertRaises(ValidationError): Language.objects.get(language_code="en").delete()
    def test_english_fallback_metadata(self):
        self._translation("en",title="English translated title"); response=self.client.get("/api/citizen/guidelines/",{"language":"ceb"}); row=response.data["results"][0]; self.assertEqual(row["title"],"English translated title"); self.assertEqual(row["returned_language"],"en"); self.assertTrue(row["used_fallback"])
    def test_filipino_and_bisaya_translation_retrieval(self):
        self._translation("fil",title="Kaligtasan sa Baha"); self._translation("ceb",title="Kaluwasan sa Baha")
        self.assertEqual(self.client.get("/api/citizen/guidelines/",{"language":"fil"}).data["results"][0]["title"],"Kaligtasan sa Baha")
        self.assertEqual(self.client.get("/api/citizen/guidelines/",{"language":"ceb"}).data["results"][0]["title"],"Kaluwasan sa Baha")
    def test_draft_and_archived_translations_are_excluded(self):
        self._translation("fil",status="Draft",title="Draft Filipino"); row=self.client.get("/api/citizen/guidelines/",{"language":"fil"}).data["results"][0]; self.assertEqual(row["title"],self.guideline.title); self.assertTrue(row["used_fallback"])
        t=GuidelineTranslation.objects.get(language__language_code="fil"); t.status="Archived"; t.save(); self.assertNotEqual(self.client.get("/api/citizen/guidelines/",{"language":"fil"}).data["results"][0]["title"],"Draft Filipino")
    def test_duplicate_translation_prevented(self):
        self._translation("fil")
        with self.assertRaises(IntegrityError): self._translation("fil")
    def test_translation_publication_and_version_increment(self):
        t=self._translation("fil",status="Draft"); old=t.version; t.translated_content="updated"; t.save(); self.assertEqual(t.version,old+1); self.auth(); result=self.client.post(f"/api/responder/guideline-translations/{t.pk}/publish/"); self.assertEqual(result.status_code,200); self.assertEqual(result.data["status"],"Published")
    def test_copy_english_translation_starting_point(self):
        english=self._translation("en",title="English source"); self.auth(); result=self.client.post("/api/responder/guideline-translations/copy-english/",{"guideline":str(self.guideline.pk),"language":"fil"},format="json"); self.assertEqual(result.status_code,201); self.assertEqual(result.data["translated_title"],english.translated_title); self.assertEqual(result.data["status"],"Draft")
    def test_offline_filipino_and_bisaya_manifests(self):
        self._translation("fil",title="Filipino offline"); self._translation("ceb",title="Bisaya offline")
        for code,title in [("fil","Filipino offline"),("ceb","Bisaya offline")]:
            data=self.client.get(f"/api/citizen/guidelines/{self.guideline.slug}/offline-manifest/",{"language":code}).data; self.assertEqual(data["requested_language"],code); self.assertEqual(data["returned_language"],code); self.assertEqual(data["title"],title); self.assertGreaterEqual(data["translation_version"],1); self.assertIn("total_download_size",data)
    def test_language_specific_video_and_caption(self):
        media=GuidelineMedia.objects.create(guideline=self.guideline,media_type="video",title="Original video",description="Original",media_file=SimpleUploadedFile("original.mp4",b"video"))
        GuidelineMediaTranslation.objects.create(media=media,language=Language.objects.get(language_code="ceb"),translated_title="Bisaya video",translated_description="Deskripsyon",caption_text="Bisaya caption",alternative_media_file=SimpleUploadedFile("bisaya.mp4",b"bisaya video"),subtitle_file=SimpleUploadedFile("bisaya.vtt",b"WEBVTT\n"),status="Published")
        row=self.client.get("/api/citizen/guidelines/",{"language":"ceb"}).data["results"][0]["media"][0]; self.assertEqual(row["title"],"Bisaya video"); self.assertEqual(row["caption_text"],"Bisaya caption"); self.assertIn("bisaya",row["media_url"]); self.assertIn("bisaya",row["subtitle_url"])
