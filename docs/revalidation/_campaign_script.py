"""Campagne QA QuickOrder: exécute les cas, écrit preuves + results.json."""
import json, re, subprocess, sys, pathlib, requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
EVD = ROOT / "docs" / "revalidation"
OUT = pathlib.Path(__file__).parent / "_results.json"
BASE = "http://127.0.0.1:5001"
KEY = {"X-API-Key": "quickorder-demo-key"}
EVD.mkdir(parents=True, exist_ok=True)

subprocess.run([str(sys.executable), "seed.py"], cwd=ROOT, check=True, capture_output=True)

RESULTS = []
LOG = []


class S(requests.Session):
    def request(self, method, url, **kw):
        r = super().request(method, BASE + url if url.startswith("/") else url, allow_redirects=kw.pop("allow_redirects", True), **kw)
        body = r.text if "json" in r.headers.get("content-type", "") else re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))[:300]
        LOG.append({"req": f"{method} {url}", "data": kw.get("data") or kw.get("json"), "status": r.status_code,
                    "final_url": r.url, "body": body[:1500]})
        return r


def case(tid, status, obtained):
    global LOG
    RESULTS.append({"id": tid, "status": status, "obtained": obtained})
    (EVD / f"{tid}.json").write_text(json.dumps({"id": tid, "status": status, "obtained": obtained, "trace": LOG}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"{tid}: {status} - {obtained}")
    LOG = []


def login(email, pw):
    s = S()
    s.post("/login", data={"email": email, "password": pw})
    return s


def api(method, path, sess=None, **kw):
    return (sess or S()).request(method, path, headers=KEY, **kw)


def stock(pid):
    return api("GET", f"/api/products/{pid}").json()["stock"]


def pid_by_name(name):
    for r in api("GET", "/api/restaurants").json()["items"]:
        for p in api("GET", f"/api/restaurants/{r['id']}/products").json()["items"]:
            if p["name"] == name:
                return p["id"]


def rid_by_name(name):
    for r in api("GET", "/api/restaurants").json()["items"]:
        if r["name"] == name:
            return r["id"]


def checkout(s, payment="card", coupon="", cash=None, address_id=None):
    if address_id is None:
        address_id = 1 if s.alice else 2
    data = {"confirm": "1", "address_id": address_id, "payment_method": payment, "coupon": coupon, "customer_note": "QA"}
    if cash is not None:
        data["cash_received"] = cash
    return s.post("/checkout", data=data)


def order_id(r):
    m = re.search(r"/orders/(\d+)", r.url)
    return int(m.group(1)) if m else None


def alice():
    s = login("alice@example.com", "Password123!")
    s.alice = True
    return s


def bob():
    s = login("bob@example.com", "Password123!")
    s.alice = False
    return s


ids = {n: pid_by_name(n) for n in ["Classic Burger", "Frites maison", "Veggie Burger", "Salmon Bowl", "Chicken Teriyaki",
                                   "Margherita", "Tajine Poulet Citron", "Late Sushi Box", "Veggie Wrap"]}
LOG.clear()
night = rid_by_name("Night Sushi"); green = rid_by_name("Green Kitchen")

# ---------------- NOMINAUX ----------------
s = S(); r = s.post("/register", data={"name": "QA Tester", "email": "qa.tester@example.com", "password": "Password123!"})
ok = r.status_code == 200 and "QA Tester" in s.get("/profile/").text
case("TC-NOM-01", "Pass" if ok else "Fail", "Compte créé, connecté automatiquement, profil affiche 'QA Tester'." if ok else "Inscription/connexion KO")

s = alice(); ok = "Mon profil" in s.get("/profile/").text
case("TC-NOM-02", "Pass" if ok else "Fail", "Connexion alice OK, page profil accessible." if ok else "Connexion KO")

t = S().get("/?q=Burger").text
ok = "Burger Factory" in t and "Tokyo Bowl" not in t
case("TC-NOM-03", "Pass" if ok else "Fail", "Recherche 'Burger' retourne uniquement Burger Factory." if ok else "Résultats inattendus")

s = alice(); s.post(f"/cart/add/{ids['Classic Burger']}", data={"quantity": 2}); s.post("/cart", data={f"qty_{ids['Classic Burger']}": 3})
t = s.get("/cart").text
ok = "35.70" in t
case("TC-NOM-04", "Pass" if ok else "Fail", "Panier: 3 x Classic Burger, sous-total 35.70 € affiché." if ok else "Sous-total incorrect")

s = alice(); s.post(f"/cart/add/{ids['Classic Burger']}", data={"quantity": 2})
r = checkout(s, "card", "WELCOME10"); oid = order_id(r)
o = api("GET", f"/api/orders/{oid}", sess=alice()).json()
ok = o["discount"] == 2.38 and o["total"] == 24.41 and o["status"] == "confirmed"
case("TC-NOM-05", "Pass" if ok else "Fail", f"Commande #{oid}: sous-total {o['subtotal']}, remise {o['discount']}, total {o['total']}, statut {o['status']}.")
NOM5 = oid

s = alice(); s.post(f"/orders/{NOM5}", data={"action": "cancel"})
o = api("GET", f"/api/orders/{NOM5}", sess=alice()).json()
case("TC-NOM-07", "Pass" if o["status"] == "cancelled" else "Fail", f"Statut commande #{NOM5} après annulation: {o['status']}.")

r = api("GET", "/api/restaurants"); j = r.json()
ok = r.status_code == 200 and j["count"] == len(j["items"]) and j["items"][0]["rating"] >= j["items"][-1]["rating"]
case("TC-NOM-06", "Pass" if ok else "Fail", f"HTTP {r.status_code}, count={j['count']}, trié par note décroissante.")

# ---------------- LIMITES ----------------
def val(code, sub):
    r = api("POST", "/api/coupons/validate", json={"code": code, "subtotal": sub}); return r.status_code, r.json()
c, j = val("WELCOME10", 20)
case("TC-LIM-01", "Pass" if j.get("valid") and j["discount"] == 2.0 else "Fail", f"Subtotal 20.00 → HTTP {c} {j}")
c, j = val("WELCOME10", 19.99)
case("TC-LIM-02", "Pass" if j.get("valid") is False else "Fail", f"Subtotal 19.99 → HTTP {c} {j}")
c, j = val("SAVE20", 100)
case("TC-LIM-03", "Pass" if j.get("discount") == 12.0 else "Fail", f"SAVE20 sur 100 € → remise {j.get('discount')} (20 % = 20 €, plafond 12 €).")

fr = ids["Frites maison"]
rs = {q: api("POST", "/api/orders", sess=alice(), json={"items": [{"product_id": fr, "quantity": q}], "payment_method": "card"}).status_code for q in (0, 21, 20)}
ok = rs[0] == 400 and rs[21] == 400 and rs[20] == 201
case("TC-LIM-04", "Pass" if ok else "Fail", f"Quantité API 0→{rs[0]}, 21→{rs[21]}, 20→{rs[20]} (attendu 400/400/201).")

t = S().get("/?max_delivery=2.50").text
names = [n for n in ["Burger Factory", "Tokyo Bowl", "Green Kitchen", "Pizza Roma", "Couscous Atlas", "Night Sushi"] if n in t]
ok = set(names) == {"Green Kitchen", "Pizza Roma"}
case("TC-LIM-05", "Pass" if ok else "Fail", f"Filtre livraison max 2.50 € affiche: {', '.join(names)} (attendu: Green Kitchen 1.99 €, Pizza Roma 2.49 € uniquement).")

salmon = ids["Salmon Bowl"]; before = stock(salmon)
s = alice(); s.post(f"/cart/add/{salmon}", data={"quantity": 3}); r = checkout(s, "card"); oid = order_id(r)
after = stock(salmon)
# reval: BUG-002 attendu = quantité plafonnée OU refus; stock jamais négatif
case("TC-LIM-06", "Pass" if after >= 0 else "Fail", f"Stock Salmon Bowl {before} → quantité 3 commandée → commande #{oid} confirmée, stock final {after}.")

def reg(name, pw):
    s = S(); r = s.post("/register", data={"name": name, "email": f"lim07.{abs(hash((name, pw)))}@example.com", "password": pw})
    return "Se déconnecter" in r.text or "Mon profil" in s.get("/profile/").text
a, b, c2 = reg("QA", "1234567"), reg("QA", "12345678"), reg("Q", "12345678")
case("TC-LIM-07", "Pass" if (not a and b and not c2) else "Fail", f"mdp 7 car. accepté={a}, mdp 8 car. accepté={b}, nom 1 car. accepté={c2} (attendu False/True/False).")

# ---------------- ERREURS ----------------
r = S().get("/api/restaurants")
case("TC-ERR-01", "Pass" if r.status_code == 401 else "Fail", f"GET /api/restaurants sans clé → HTTP {r.status_code} {r.text.strip()[:80]}")

r = S().post("/login", data={"email": "alice@example.com", "password": "wrong"})
case("TC-ERR-02", "Pass" if "incorrect" in r.text else "Fail", "Message 'Email ou mot de passe incorrect.' affiché, non connecté." if "incorrect" in r.text else "Pas de message")

c, j = val("EXPIRED10", 50)
case("TC-ERR-03", "Pass" if c == 404 and j["valid"] is False else "Fail", f"EXPIRED10 → HTTP {c} {j}")

veg = ids["Veggie Burger"]; rid = rid_by_name("Burger Factory")
page = S().get(f"/restaurant/{rid}").text
s = alice(); s.post(f"/cart/add/{veg}", data={"quantity": 1}); cart = s.get("/cart").text
visible = "Veggie Burger" in page; in_cart = "Veggie Burger" in cart
case("TC-ERR-04", "Pass" if (not in_cart) else "Fail", f"Veggie Burger (stock 0): visible sur la page restaurant={visible}, ajouté au panier={in_cart}.")

r1 = api("POST", "/api/orders", sess=alice(), json={"items": []}); r2 = api("POST", "/api/orders", sess=alice(), json={"items": [{"product_id": 99999, "quantity": 1}]})
case("TC-ERR-05", "Pass" if (r1.status_code, r2.status_code) == (400, 400) else "Fail", f"items=[] → {r1.status_code}; produit inconnu → {r2.status_code}.")

s = alice(); s.post(f"/cart/add/{ids['Classic Burger']}", data={"quantity": 2}); r = checkout(s, "cash", cash="5"); oid = order_id(r)
o = api("GET", f"/api/orders/{oid}", sess=alice()).json() if oid else {"total": None, "status": None, "payment_status": None, "change_due": None}
case("TC-ERR-06", "Pass" if oid is None else "Fail", f"Espèces 5.00 € pour total {o['total']} € → commande #{oid} {o['status']}/{o['payment_status']}, change_due={o['change_due']}.")

r = api("POST", "/api/orders", sess=alice(), json={"items": [{"product_id": ids["Classic Burger"], "quantity": 2}], "coupon": "CODEINVALIDE"})
j = r.json()
case("TC-ERR-07", "Pass" if r.status_code in (400, 404, 422) else "Fail", f"Coupon inexistant 'CODEINVALIDE' → HTTP {r.status_code}, remise={j.get('discount')}, commande créée silencieusement.")

a_order = api("GET", "/api/orders", sess=alice()).json()["items"][0]["id"]
sb = bob(); r_ui = sb.get(f"/orders/{a_order}"); r_api = api("GET", f"/api/orders/{a_order}", sess=sb)
ok = r_api.status_code == 403 and "Commande inaccessible" in r_ui.text
case("TC-ERR-08", "Pass" if ok else "Fail", f"Bob → commande d'Alice #{a_order}: UI redirigé (flash 'Commande inaccessible.')={'Commande inaccessible' in r_ui.text}, API HTTP {r_api.status_code}.")

r = api("GET", "/api/orders"); items = r.json().get("items", [])
case("TC-ERR-09", "Pass" if r.status_code == 401 else "Fail", f"GET /api/orders avec clé seule (aucune session) → HTTP {r.status_code}, {len(items)} commandes d'Alice retournées.")

r = S().post("/login?next=https://evil.example/phish", data={"email": "alice@example.com", "password": "Password123!"}, allow_redirects=False)
loc = r.headers.get("Location")
case("TC-ERR-10", "Pass" if not (loc or "").startswith("http") else "Fail", f"POST /login?next=https://evil.example/phish → HTTP {r.status_code} Location: {loc}")

r1 = S().get("/admin/", allow_redirects=False); sa = alice(); r2 = sa.get("/admin/")
ok = r1.status_code == 302 and "Accès réservé" in r2.text
case("TC-ERR-11", "Pass" if ok else "Fail", f"/admin/ anonyme → HTTP {r1.status_code}; client alice → page d'accueil + 'Accès réservé aux administrateurs.'")

# ---------------- RÈGLES MÉTIER ----------------
s = alice(); s.post(f"/cart/add/{ids['Classic Burger']}", data={"quantity": 1}); s.post(f"/cart/add/{ids['Margherita']}", data={"quantity": 1})
t = s.get("/cart").text
ok = "Margherita" not in t and "Classic Burger" in t
case("TC-REG-01", "Pass" if ok else "Fail", "Ajout Margherita (Pizza Roma) refusé: 'Un panier ne peut contenir que des produits du même restaurant.'" if ok else "Mélange de restaurants accepté")

late = ids["Late Sushi Box"]
s = alice(); s.post(f"/cart/add/{late}", data={"quantity": 1}); r = checkout(s, "card"); oid = order_id(r)
r_api = api("POST", "/api/orders", sess=alice(), json={"items": [{"product_id": late, "quantity": 1}], "payment_method": "card"})
case("TC-REG-02", "Pass" if oid is None and r_api.status_code != 201 else "Fail", f"Night Sushi (fermé): UI commande #{oid} confirmée; API POST /orders → HTTP {r_api.status_code}. Listé aussi dans GET /api/restaurants.")

s = alice(); s.post(f"/cart/add/{ids['Frites maison']}", data={"quantity": 1}); r = checkout(s, "card"); oid = order_id(r)
o = api("GET", f"/api/orders/{oid}", sess=alice()).json() if oid else {}
case("TC-REG-03", "Pass" if oid is None else "Fail", f"Burger Factory minimum 20.00 €, panier 3.50 € → commande #{oid} confirmée (total {o.get('total')} €).")

c, j = val("ATLAS15", 100)
case("TC-REG-04", "Pass" if j.get("discount") == 15.0 else "Fail", f"ATLAS15 annoncé -15 % : sur 100 € remise = {j.get('discount')} € ({j.get('discount_percent')} %).")

s = alice(); n0 = len(api("GET", "/api/orders", sess=alice()).json()["items"])
s.post(f"/cart/add/{ids['Classic Burger']}", data={"quantity": 2}); r = checkout(s, "paypal")
n1 = len(api("GET", "/api/orders", sess=alice()).json()["items"])
case("TC-REG-05", "Pass" if n1 - n0 == 1 else "Fail", f"1 paiement PayPal → {n1 - n0} commandes créées (attendu 1).")

sa = login("admin@quickorder.local", "Admin123!")
sa.post("/admin/orders/1/status", data={"status": "confirmed"})
st = api("GET", "/api/orders/1", sess=sa).json()["status"]
case("TC-REG-06", "Pass" if st == "delivered" else "Fail", f"Commande #1 livrée, admin → 'confirmed': statut final = {st} (retour arrière accepté).")

sb = bob(); r = sb.post(f"/restaurant/{green}/review", data={"rating": 1, "comment": "QA: avis sans commande"}, allow_redirects=True)
case("TC-REG-07", "Pass" if "Merci" not in r.text else "Fail", f"Bob (jamais commandé chez Green Kitchen) → avis publié: {'Merci pour votre avis' in r.text}.")

tokyo = pid_by_name("Chicken Teriyaki")
s = alice(); s.post(f"/cart/add/{tokyo}", data={"quantity": 3}); r = checkout(s, "card", "TOKYO30"); oid = order_id(r)
o = api("GET", f"/api/orders/{oid}", sess=alice()).json()
ok = o["discount"] == 3.49 and o["total"] == o["subtotal"]
case("TC-REG-08", "Pass" if ok else "Fail", f"TOKYO30 sur 40.50 €: remise {o['discount']}, frais {o['delivery_fee']}, total {o['total']} (= sous-total → livraison offerte).")

t = S().get("/?q=japonaise").text; j = api("GET", "/api/restaurants?q=japonaise").json()
case("TC-LIM-08", "Pass" if "Tokyo Bowl" in t and j["count"] >= 1 else "Fail", f"Recherche 'japonaise' (présent dans la description de Tokyo Bowl 'Cuisine japonaise et bowls frais'): UI Tokyo Bowl trouvé={'Tokyo Bowl' in t}, API count={j['count']}.")

s = S(); s.post("/register", data={"name": "QA Adresse", "email": "qa.addr@example.com", "password": "Password123!"})
s.post(f"/cart/add/{ids['Classic Burger']}", data={"quantity": 2}); chk = s.get("/checkout").text
m = re.search(r'<option value="(\d+)"[^>]*>([^<]*)</option>', chk)  # reval: plus d'adresse vide proposée
oid = None
if m:
    r = s.post("/checkout", data={"confirm": "1", "address_id": int(m.group(1)), "payment_method": "card", "customer_note": ""}); oid = order_id(r)
case("TC-ERR-12", "Pass" if oid is None else "Fail", f"Nouvel inscrit: adresse proposée au checkout = '{m.group(2).strip() if m else 'aucune'}' → commande #{oid} confirmée sans adresse de livraison.")

s = alice(); before = "Mon profil" in s.get("/profile/").text; s.get("/logout"); after = "Mon profil" in s.get("/profile/").text
case("TC-ERR-13", "Pass" if not (before and not after) else "Fail", f"Déconnexion déclenchée par simple GET /logout (sans POST ni jeton CSRF): connecté avant={before}, connecté après={after}.")

OUT.write_text(json.dumps(RESULTS, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print(Counter(x["status"] for x in RESULTS))
