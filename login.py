#!/usr/bin/env python3
"""
AgriStack Multi-State Token Manager — RENDER READY
"""

import os, sys, json, time, base64, re, uuid, logging, threading
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote
import requests
from bs4 import BeautifulSoup
from PIL import Image
import ddddocr
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("agristack")

ocr = ddddocr.DdddOcr(show_ad=False)

RSA_PUB_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC9BLl8HcSzbdYg5S50RfMznsJf
zzefjAUuYkWS9vViuzs4vw59bbEsIu4bjAlyyTusg8luuXPA9SvO4zYgj1rxe42f
i+tISEuwIcL0f0I+PgmbIBPOhSnTVYmXFmtbZxXgSfLYyzq0WGNZDLJ0s5V1cE6e
EFTb/F6ZCp79sd+/UQIDAQAB
-----END PUBLIC KEY-----"""

STATE_CONFIG = {
    "AP": {"full": "apfr", "sub": "ap"},
    "AS": {"full": "asfr", "sub": "as"},
    "BR": {"full": "bhfr", "sub": "bh"},
    "CG": {"full": "cgfr", "sub": "cg"},
    "GJ": {"full": "gjfr", "sub": "gj"},
    "HP": {"full": "hpfr", "sub": "hp"},
    "HR": {"full": "hrfr", "sub": "hr"},
    "KL": {"full": "klfr", "sub": "kl"},
    "MH": {"full": "mhfr", "sub": "mh"},
    "MP": {"full": "mpfr", "sub": "mp"},
    "OD": {"full": "odfr", "sub": "od"},
    "PB": {"full": "pbfr", "sub": "pb"},
    "RJ": {"full": "rjfr", "sub": "rj"},
    "TN": {"full": "tnfr", "sub": "tn"},
    "TR": {"full": "trfr", "sub": "tr"},
    "UK": {"full": "ukfr", "sub": "uk"},
    "UP": {"full": "upfr", "sub": "up"},
}

ALL_STATES = sorted(STATE_CONFIG.keys())
PARALLEL_WORKERS = 3
REFRESH_INTERVAL = 5

_token_cache = {}
_cache_lock = threading.Lock()

def cache_set(state, user_token, auth_token, expires_in):
    with _cache_lock:
        _token_cache[state.upper()] = {
            'user_token': user_token,
            'auth_token': auth_token or '',
            'expires': time.time() + expires_in - 60
        }

def cache_get(state):
    with _cache_lock:
        data = _token_cache.get(state.upper())
        if data and data['expires'] > time.time():
            return data
        return None

CSC_CREDENTIALS = [
    {"id": "337327750017", "password": "Mktl@143"},
    {"id": "642453380016", "password": "Channi@111"},
    {"id": "263544510015", "password": "Ramram@1991"},
    {"id": "571673270017", "password": "Manisha@543213"},
    {"id": "675671150014", "password": "@iamAjay1985"},
    {"id": "427734410018", "password": "298192"},
    {"id": "747367760019", "password": "577503"},
    {"id": "177572310015", "password": "Rajan@6363"},
    {"id": "241165340011", "password": "Nace@750"},
    {"id": "719926500016", "password": "Guddu@4048"},
    {"id": "740179770010", "password": "Welcome@2024*"},
    {"id": "427666210012", "password": "Anupam@52"},
    {"id": "636345540017", "password": "SshobhaKR2030@"},
    {"id": "732347240015", "password": "Lokesh@3007"},
    {"id": "462163420015", "password": "Himanshu@2601"},
    {"id": "316746330018", "password": "Sanni@#2006"},
    {"id": "331413150016", "password": "Enter@456"},
    {"id": "736456360018", "password": "Siwan@2255"},
    {"id": "353939590014", "password": "Shreeji@6600"},
    {"id": "473838030050", "password": "Sunny2527#"},
    {"id": "725124320011", "password": "780046"},
    {"id": "663734750018", "password": "Avadh@123"},
    {"id": "243773650014", "password": "Singot@123"},
    {"id": "527433350016", "password": "Mahira143$"},
    {"id": "241165340024", "password": "Lalit@123"},
    {"id": "321212540018", "password": "Amit@2255"},
    {"id": "473573670012", "password": "Admin@1242"},
    {"id": "731431250010", "password": "Vijay@1996"},
    {"id": "362771160019", "password": "Razzkushwah@33"},
    {"id": "234476620015", "password": "Sonar01@"},
    {"id": "577553540019", "password": "722761"},
    {"id": "224115260016", "password": "Kajal@32"},
    {"id": "234814420017", "password": "718445"},
    {"id": "311162440011", "password": "Dec@124542"},
    {"id": "676657210015", "password": "Subal@2022"},
    {"id": "415627560010", "password": "Lalananand$1995"},
    {"id": "263555470010", "password": "Mirajul@123"},
    {"id": "645365560019", "password": "Yachi@1991"},
    {"id": "252623160018", "password": "Deepak@123"},
    {"id": "557732550011", "password": "Upasna@1998"},
    {"id": "573453250017", "password": "Kings@1122"},
    {"id": "271316170013", "password": "Adithya@201029"},
    {"id": "634225650019", "password": "Mahesh@1234"},
    {"id": "653265130018", "password": "Sahir@10042020"},
    {"id": "375518020017", "password": "Balu@@2024"},
    {"id": "657242450019", "password": "Raushan@1234"},
    {"id": "513271240015", "password": "Ku@721135"},
    {"id": "330904830015", "password": "Avit@120"},
    {"id": "7205453095", "password": "Moti@123"},
    {"id": "230451000015", "password": "Omsairam9*"},
    {"id": "517542470057", "password": "Gmail.com"},
    {"id": "953272080290", "password": "An@163823"},
    {"id": "7013770643", "password": "Para1166@"},
    {"id": "564523760018", "password": "399834"},
    {"id": "456161450013", "password": "Ratan@2025"},
    {"id": "467114720016", "password": "Abhijit@1"},
    {"id": "656354370016", "password": "Gondiya@0001"},
    {"id": "655242110018", "password": "Bhavesh@1999"},
    {"id": "7869362187", "password": "Krishna12@"},
    {"id": "543420820014", "password": "saidul009"},
    {"id": "653545540011", "password": "@Bschool*810"},
    {"id": "87557", "password": "Sarthak@2012"},
    {"id": "311535610013", "password": "Rinku@123"},
    {"id": "225714150014", "password": "Asn@6446"},
    {"id": "236525660017", "password": "Rahul@123"},
    {"id": "536473710011", "password": "nandanW@12"},
    {"id": "774676270013", "password": "Pass@123"},
    {"id": "532472610018", "password": "Ram@123456"},
    {"id": "571555310011", "password": "Shaki@79038"},
    {"id": "251536530016", "password": "Sanjay@321"},
    {"id": "312167630011", "password": "tanmay2008"},
    {"id": "653142340013", "password": "Samyu@22"},
    {"id": "471424530011", "password": "Love@1234"},
    {"id": "717650270013", "password": "Pushpa@2018"},
    {"id": "524572260017", "password": "Krishna7"},
    {"id": "759405550019", "password": "Shivani@54321"},
    {"id": "263617170016", "password": "Roshk@4599"},
    {"id": "371663670017", "password": "admin@123"},
    {"id": "646114410024", "password": "674913"},
    {"id": "442245320013", "password": "BHANUPRIYA2010"},
    {"id": "622262220016", "password": "2330"},
    {"id": "265524420016", "password": "Parmar@123"},
    {"id": "532255360010", "password": "Freedom@1947"},
    {"id": "269176460018", "password": "9304980771"},
    {"id": "324257250018", "password": "Pritam1994"},
    {"id": "273226440012", "password": "@Jmakrand123"},
    {"id": "221315360014", "password": "Sumathi@123"},
    {"id": "233357120015", "password": "Makrand@1985"},
    {"id": "421235230022", "password": "131225"},
    {"id": "413126640014", "password": "Muke@2002"},
    {"id": "9824223411", "password": "82286378"},
    {"id": "640762820017", "password": "@nubhav123"},
    {"id": "420167870011", "password": "123456789"},
    {"id": "531616220012", "password": "&@_5p+#Eh.ez!Rk$$"},
    {"id": "192059060019", "password": "@Gourish3123"},
    {"id": "247564770012", "password": "Shad@123"},
    {"id": "273421530012", "password": "Db@17@86#"},
    {"id": "223677210012", "password": "None"},
    {"id": "265524470018", "password": "1180345594185076736"},
    {"id": "221712150012", "password": "Jina#2211"},
    {"id": "323666660013", "password": "8121585961"},
    {"id": "213477230014", "password": "Madan@234"},
    {"id": "656614450017", "password": "Ary@1234"},
    {"id": "136321560019", "password": "zxcvbnm,."},
    {"id": "656752370014", "password": "2213"},
    {"id": "715331660019", "password": "Borah@1985"},
    {"id": "456356510013", "password": "Rishav@12345"},
    {"id": "732412420013", "password": "Deepak@702"},
    {"id": "217671110014", "password": "565404"},
    {"id": "320024150017", "password": "Deepak@2002"},
    {"id": "277632610011", "password": "Linta@9876"},
    {"id": "253641320065", "password": "Si@553618"},
    {"id": "221413230018", "password": "Aabid@1159"},
    {"id": "133613540043", "password": "Patx@7667"},
    {"id": "324767130017", "password": "Amrita123"},
    {"id": "154255560019", "password": "Mohit@123"},
    {"id": "571273170019", "password": "nEJAM%93"},
    {"id": "272542450014", "password": "Allah$1411"},
    {"id": "542612720015", "password": "AgarsS@123"},
    {"id": "574131210010", "password": "632413"},
    {"id": "353136140014", "password": "DpP7BwVgKz"},
    {"id": "276352520010", "password": "New@1234"},
    {"id": "437713620018", "password": "Taveel@1007"},
    {"id": "636465270017", "password": "XJuaWX95mo"},
    {"id": "415173550010", "password": "Shiv9634#"},
    {"id": "373436610018", "password": "Dwip5683@12"},
    {"id": "125176420011", "password": "Ramu8254"},
    {"id": "267513510010", "password": "Raj@951981"},
    {"id": "122414320012", "password": "Cpvi@1946"},
    {"id": "257514530019", "password": "@DELHI123"},
    {"id": "732412420013", "password": "Asdf@7788"},
    {"id": "247453650030", "password": "Zi@391104"},
    {"id": "633844510011", "password": "Ajay@0000"},
    {"id": "326657510011", "password": "Nikhil@123"},
    {"id": "452005510016", "password": "Vimal@12345"},
    {"id": "319237020019", "password": "0fRXqDeXOS"},
    {"id": "313333450012", "password": "Rashid#1234"},
    {"id": "257514530019", "password": "CG2YmkeFmK"},
    {"id": "271316170013", "password": "Feb@1111"},
    {"id": "514686620013", "password": "Sachi*Fn@123"},
    {"id": "535213560012", "password": "9651217318n"},
    {"id": "312257", "password": "420014:rpPQN4X2myReQgC"},
    {"id": "234764170014", "password": "Pratik@7085"},
    {"id": "426472150011", "password": "Yadav@70364"},
    {"id": "514686620013", "password": "SachiKsn@123"},
    {"id": "534527330018", "password": "186"},
    {"id": "542612720015", "password": "AgarV.@123"},
    {"id": "542612720015", "password": "Agar#E@123"},
    {"id": "635351150018", "password": "Lalji@5835"},
    {"id": "121614470017", "password": "DEOdha@123"},
    {"id": "551664610017", "password": "Sulen@123"},
    {"id": "551664610017", "password": "Sulen@123456"},
    {"id": "651154520012", "password": "Raj@123456sd"},
    {"id": "542612720015", "password": "Agar#%@123"},
    {"id": "121614470017", "password": "RAMprasad@2650"},
    {"id": "318119310023", "password": "323965"},
    {"id": "124535140012", "password": "Roh@7703"},
    {"id": "726137210013", "password": "Purna@702"},
    {"id": "245791710019", "password": "Ak127*123"},
    {"id": "514686620013", "password": "SachiBmn@123"},
    {"id": "571273170019", "password": "Nejam@1993"},
    {"id": "717626260016", "password": "423402"},
    {"id": "313434710015", "password": "Dkp@081996"},
    {"id": "699017580015", "password": "Shiva@12345"},
    {"id": "145231630011", "password": "Binit@123!!"},
    {"id": "271316170013", "password": "dg1234"},
    {"id": "773767510016", "password": "Anjali@123"},
    {"id": "534527330018", "password": "suvrat_patel"},
    {"id": "379614170015", "password": "Nifty@798546"},
    {"id": "121614470017", "password": "848282"},
    {"id": "651154520012", "password": "hCN7uNma4z"},
    {"id": "721267370017", "password": "binish@KU789"},
    {"id": "314351610013", "password": "Dinesh@108"},
    {"id": "377366420015", "password": "Akhilesh@12"},
    {"id": "163655740079", "password": "SAmrat@12"},
    {"id": "659007030062", "password": "Re@802214"},
    {"id": "245726210012", "password": "Ranjan@1281"},
    {"id": "763661670016", "password": "Csc@919961"},
    {"id": "414367660015", "password": "Ngds@1432"},
    {"id": "363266770019", "password": "Baban@123"},
    {"id": "756543710011", "password": "0077@Krunal"},
    {"id": "163655740014", "password": "Dpk@1992"},
    {"id": "226525450016", "password": "Rohan@1234"},
    {"id": "635351150018", "password": "Maharaj@123"},
    {"id": "277123110017", "password": "Ashok@108"},
    {"id": "621225420010", "password": "ranjan@KU123"},
    {"id": "264656510018", "password": "DigiTech@123"},
    {"id": "471117740017", "password": "STcsc@786"},
    {"id": "226423240011", "password": "Murtaza@700611"},
    {"id": "642241250014", "password": "Anish@5620"},
    {"id": "516256450013", "password": "Vikram@9800"},
    {"id": "432141670016", "password": "Oaktree@2020"},
    {"id": "367563620017", "password": "Kiran@1995"},
    {"id": "656262110017", "password": "@Reeshu201220"},
    {"id": "261547750010", "password": "Mahakal@8055"},
    {"id": "255247140011", "password": "187229"},
    {"id": "621225420010", "password": "ranjan@KU789"},
    {"id": "451522670030", "password": "Da@673157"},
    {"id": "537553320032", "password": "Ab@620234"},
    {"id": "216174140015", "password": "Arand@123"},
    {"id": "451522670024", "password": "Deepak@72549"},
    {"id": "245726210077", "password": "Bi@941029"},
    {"id": "677272640012", "password": "Sonu@1990"},
    {"id": "563125130019", "password": "Dhrumil@143"},
    {"id": "446512320010", "password": "Indur@1234"},
    {"id": "646522430017", "password": "AmitHH@200"},
    {"id": "135346720016", "password": "212941"},
    {"id": "342385690019", "password": "355862"},
    {"id": "451522670011", "password": "Nidhi@1989"},
    {"id": "326435720019", "password": "Rahul@2536"},
    {"id": "712047190017", "password": "Shiva@660508"},
    {"id": "293802940042", "password": "Lokesh51#"},
    {"id": "236415210013", "password": "Vik@7772"},
    {"id": "572633520010", "password": "B@raj5591"},
    {"id": "262227760019", "password": "895811"},
    {"id": "376115760023", "password": "Bhanuraj@123"},
    {"id": "445723610012", "password": "Harry@7719"},
    {"id": "126274410014", "password": "Vinod@1983"},
    {"id": "427453430012", "password": "123456@Pr"},
    {"id": "522756270013", "password": "Rohim998@"},
    {"id": "642752560015", "password": "Mantu@1316"},
    {"id": "719150110016", "password": "923300"},
    {"id": "689727220013", "password": "396033"},
    {"id": "363775220018", "password": "533729"},
    {"id": "374215650045", "password": "pa@714590"},
    {"id": "374215650013", "password": "814102"},
    {"id": "374215650013", "password": "Anand@143"},
    {"id": "524457340014", "password": "Pavan@1234"},
    {"id": "674412230016", "password": "Ridhi*864983"},
    {"id": "261676560016", "password": "Chetan@1988"},
    {"id": "531163330019", "password": "Jayanna@123"},
    {"id": "265563270010", "password": "1@Rajinderjeet"},
    {"id": "265563270010", "password": "1@Saroay"},
    {"id": "466416140017", "password": "Prah@123"},
    {"id": "765972820018", "password": "Easy7607shop#"},
    {"id": "724411150018", "password": "Irn@89575810"},
    {"id": "361767170014", "password": "Sabir@786"},
    {"id": "371523360011", "password": "581819"},
    {"id": "647156530012", "password": "Sabir@786786"},
    {"id": "315525110019", "password": "Mubarak@786"},
    {"id": "621712410018", "password": "Abs#8210"},
    {"id": "451416630014", "password": "Tutal@1999"},
    {"id": "357003930013", "password": "Qw83<@hind"},
    {"id": "345414310010", "password": "Jannat313@"},
    {"id": "211314620018", "password": "Akant@2001"},
    {"id": "427252130013", "password": "Ram1985@"},
    {"id": "222656210016", "password": "Waheguroo@123"},
    {"id": "541317520016", "password": "Ajay@123"},
    {"id": "532653450014", "password": "Rajan@3399"},
    {"id": "125745710014", "password": "Anil@643714"},
    {"id": "271342340017", "password": "9375788212@aA"},
    {"id": "243662310012", "password": "Honda@4666"},
    {"id": "237565720012", "password": "Daksh2014@"},
    {"id": "576736320010", "password": "J@har40144"},
    {"id": "576736320023", "password": "Ka@823342"},
    {"id": "476561730011", "password": "Taju4424@1"},
    {"id": "256191700013", "password": "Nkyadav@143"},
    {"id": "133752550053", "password": "Vijaypal1@"},
    {"id": "133752550011", "password": "Laxmansi67841@"},
    {"id": "111446540040", "password": "Vipin@3268"},
    {"id": "361111250030", "password": "Ha@103688"},
    {"id": "563575560014", "password": "Sameeraale@123"},
    {"id": "631725270016", "password": "Deeksha@5438"},
    {"id": "646242270011", "password": "Pranamya@3690"},
    {"id": "551745550014", "password": "Chetan@967337"},
    {"id": "953271529805", "password": "Sh@743905"},
    {"id": "451726140019", "password": "Sunil@2002"},
    {"id": "255616340014", "password": "Bapuni@2025"},
    {"id": "255616340014", "password": "Bapuni@1997"},
    {"id": "645225220016", "password": "Bipin@12345"},
    {"id": "153918390014", "password": "Reeshi@90"},
    {"id": "635437620010", "password": "Anil@7610"},
    {"id": "344331310010", "password": "Anil@7610"},
    {"id": "434267230014", "password": "Vikas@8175"},
    {"id": "677445620017", "password": "Target@2022"},
    {"id": "344171510018", "password": "Manish@9794"},
    {"id": "645353520019", "password": "RkDk@#$998850"},
    {"id": "641736370010", "password": "Prince@153200"},
    {"id": "221412120014", "password": "316142"},
    {"id": "542371130010", "password": "Gaj@1986"},
]


def generate_dpop_keypair():
    return ec.generate_private_key(ec.SECP256R1(), default_backend())


def generate_dpop_proof(private_key, method, url):
    pub = private_key.public_key().public_numbers()
    x_b64 = base64.urlsafe_b64encode(pub.x.to_bytes(32, 'big')).rstrip(b'=').decode()
    y_b64 = base64.urlsafe_b64encode(pub.y.to_bytes(32, 'big')).rstrip(b'=').decode()
    header = {"typ": "dpop+jwt", "alg": "ES256",
              "jwk": {"kty": "EC", "crv": "P-256", "x": x_b64, "y": y_b64}}
    payload = {"jti": str(uuid.uuid4()), "htm": method.upper(),
               "htu": url, "iat": int(time.time())}
    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=').decode()
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    sig = private_key.sign(f"{h_b64}.{p_b64}".encode(), ec.ECDSA(hashes.SHA256()))
    s_b64 = base64.urlsafe_b64encode(sig).rstrip(b'=').decode()
    return f"{h_b64}.{p_b64}.{s_b64}"


def encrypt_password(rvar, user, password):
    b64_user = base64.b64encode(user.encode()).decode()
    b64_pass = base64.b64encode(password.encode()).decode()
    combined = f"{rvar}@{b64_user}@{b64_pass}"
    b64_combined = base64.b64encode(combined.encode()).decode()
    key = serialization.load_pem_public_key(RSA_PUB_KEY.encode(), backend=default_backend())
    encrypted = key.encrypt(b64_combined.encode(), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode()


def solve_captcha(b64_str):
    if "base64," in b64_str:
        b64_str = b64_str.split("base64,")[1]
    b64_str = b64_str.strip().strip('"').strip("'").split('?')[0]
    raw = base64.b64decode(b64_str)
    return ocr.classification(Image.open(BytesIO(raw)).convert("RGB"))


def try_login(state_code, csc_id, password):
    cfg = STATE_CONFIG[state_code]
    base_url = f"https://{cfg['full']}.agristack.gov.in"
    sub = cfg['sub']
    
    try:
        session = requests.Session()
        ua = "Mozilla/5.0 (Linux; Android 15; 2312FRAFDI Build/AP3A.240905.015.A2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.7827.159 Mobile Safari/537.36"
        session.headers.update({"User-Agent": ua})

        dpop_key = generate_dpop_keypair()

        url1 = f"{base_url}/farmer-registry-api-{sub}/agristack/v1/api/csc/auth/url"
        dpop = generate_dpop_proof(dpop_key, "GET", url1)
        r = session.get(url1, headers={"dpop": dpop, "accept": "application/json", "referer": f"{base_url}/farmer-registry-{sub}/"}, timeout=20)
        auth_url = r.json()["data"]
        state_val = re.search(r'state=([^&]+)', auth_url).group(1)

        r = session.get(auth_url, headers={"accept": "text/html", "referer": f"{base_url}/farmer-registry-{sub}/"}, timeout=20)
        soup = BeautifulSoup(r.text, "lxml")

        csrf_token = None
        for c in session.cookies:
            if c.name == "csrf_cookie_name":
                csrf_token = c.value
                break
        if not csrf_token:
            inp = soup.find("input", {"name": "csrf_test_name"})
            if inp:
                csrf_token = inp.get("value")

        rvar_match = re.search(r'var rvar = "(\d+)"', r.text)
        rvar = rvar_match.group(1) if rvar_match else "771129"

        captcha_b64 = None
        ci = soup.find("div", {"id": "captchaimgs"})
        if ci:
            img = ci.find("img")
            if img and img.get("src"):
                captcha_b64 = img["src"]
        if not captcha_b64:
            m = re.search(r'data:image/jpeg;base64,([A-Za-z0-9+/=]+)', r.text)
            if m:
                captcha_b64 = m.group(0)

        if not csrf_token or not captcha_b64:
            return None

        captcha = solve_captcha(captcha_b64)
        enc_pass = encrypt_password(rvar, csc_id, password)
        data = {
            "csrf_test_name": csrf_token,
            "csclogin": csc_id,
            "password": enc_pass,
            "captcha": captcha,
            "login": "Log In"
        }
        r = session.post(auth_url, data=data, headers={
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://connect.csc.gov.in",
            "referer": auth_url
        }, allow_redirects=False, timeout=20)

        if r.status_code not in [302, 303]:
            return None

        loc = r.headers.get("Location", "")
        
        auth_code = None
        code_match = re.search(r'[?&]code=([^&]+)', loc)
        if code_match:
            auth_code = code_match.group(1)
        else:
            fragment = loc.split('#', 1)[1] if '#' in loc else loc
            url_match = re.search(r'url=([^&]+)', fragment)
            if url_match:
                url_decoded = unquote(url_match.group(1))
                code_match = re.search(r'code=([^&]+)', url_decoded)
                if code_match:
                    auth_code = code_match.group(1)
            if not auth_code:
                all_codes = re.findall(r'code=([A-Za-z0-9_-]{10,})', unquote(loc))
                if all_codes:
                    auth_code = all_codes[0]
        
        if not auth_code:
            return None

        url4 = f"{base_url}/farmer-registry-api-{sub}/agristack/v1/api/csc/fr/login?code={auth_code}&state={state_val}"
        r = session.get(url4, headers={"referer": "https://connect.csc.gov.in/"}, allow_redirects=False, timeout=20)

        bearer_token = None
        if r.status_code in [302, 303, 301]:
            loc2 = r.headers.get("Location", "")
            token_match = re.search(r'token=([^&]+)', loc2)
            if token_match:
                bearer_token = token_match.group(1)

        if not bearer_token:
            r2 = session.get(url4, headers={"referer": "https://connect.csc.gov.in/"}, allow_redirects=True, timeout=20)
            if r2.url:
                token_match = re.search(r'token=([^&]+)', r2.url)
                if token_match:
                    bearer_token = token_match.group(1)
            if not bearer_token:
                token_match = re.search(r'eyJ[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+){2}', r2.text)
                if token_match:
                    bearer_token = token_match.group(0)

        if not bearer_token:
            return None

        url5 = f"{base_url}/farmer-registry-api-{sub}/agristack/v1/api/authenticate/user/token"
        dpop = generate_dpop_proof(dpop_key, "POST", url5)
        r = session.post(url5, json={"token": bearer_token}, headers={
            "authorization": f"Bearer {bearer_token}",
            "dpop": dpop,
            "content-type": "application/json",
            "origin": base_url,
            "referer": f"{base_url}/farmer-registry-{sub}/"
        }, timeout=20)

        data = r.json()
        if data.get("status") == "success":
            ud = data["data"]
            return {
                "user_token": ud["userToken"],
                "auth_token": ud.get("loginLogoutActivityLog", {}).get("authToken") or ud["userToken"],
                "expires_in": ud.get("tokenExpiresIn", 900),
                "user_id": ud.get("userId")
            }

    except Exception as e:
        log.error("[%s] %s", state_code, e)
    
    return None


def parallel_login_state(state_code):
    log.info("[%s] Parallel login starting...", state_code)
    
    winner = None
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as ex:
        futures = {ex.submit(try_login, state_code, c["id"], c["password"]): c for c in CSC_CREDENTIALS}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    winner = result
                    log.info("[%s] ✅ WINNER: %s", state_code, futures[future]["id"])
                    for f in futures:
                        f.cancel()
                    break
            except Exception:
                pass
    
    if not winner:
        log.warning("[%s] ❌ No winner found", state_code)
    
    return winner


def auto_refresh_loop(state_code):
    while True:
        try:
            cached = cache_get(state_code)
            if not cached:
                log.info("[%s] Refreshing...", state_code)
                result = parallel_login_state(state_code)
                if result:
                    cache_set(state_code, result['user_token'], result['auth_token'], result['expires_in'])
                    log.info("[%s] ✅ Cached (user=%s)", state_code, result['user_id'])
                else:
                    time.sleep(10)
                    continue
            time.sleep(REFRESH_INTERVAL)
        except Exception as e:
            log.error("[%s] %s", state_code, e)
            time.sleep(5)


app = Flask(__name__)


@app.after_request
def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "success",
        "service": "agristack-token-api",
        "states": ALL_STATES,
        "cached": list(_token_cache.keys()),
        "refresh_interval": REFRESH_INTERVAL
    })


@app.route("/states", methods=["GET"])
def list_states():
    return jsonify({"status": "success", "states": ALL_STATES})


@app.route("/<state>", methods=["GET"])
def get_token(state):
    state = state.upper()
    if state not in STATE_CONFIG:
        return jsonify({"status": False, "message": "Unknown state"}), 400
    
    cached = cache_get(state)
    if cached:
        return jsonify({
            "auth_token": cached['auth_token'],
            "state": state,
            "status": "success",
            "user_token": cached['user_token']
        })
    
    return jsonify({
        "status": False,
        "message": f"No token for {state} yet. Try /{state}/refresh"
    }), 503


@app.route("/<state>/refresh", methods=["GET", "POST"])
def refresh_token(state):
    state = state.upper()
    if state not in STATE_CONFIG:
        return jsonify({"status": False, "message": "Unknown state"}), 400
    
    result = parallel_login_state(state)
    if not result:
        return jsonify({"status": False, "message": f"Login failed for {state}"}), 502
    
    cache_set(state, result['user_token'], result['auth_token'], result['expires_in'])
    return jsonify({
        "auth_token": result['auth_token'],
        "state": state,
        "status": "success",
        "user_id": result['user_id'],
        "user_token": result['user_token']
    })


_bg_started = False
_bg_lock = threading.Lock()


def start_all_background():
    for sc in ALL_STATES:
        threading.Thread(target=auto_refresh_loop, args=(sc,), daemon=True, name=f"r-{sc}").start()
        log.info("[%s] background thread started", sc)
        time.sleep(0.5)


def ensure_bg():
    global _bg_started
    with _bg_lock:
        if not _bg_started:
            _bg_started = True
            threading.Thread(target=start_all_background, daemon=True).start()


@app.before_request
def _start_bg():
    ensure_bg()


# Render startup
ensure_bg()
