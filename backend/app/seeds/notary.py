"""Notary jurisdiction data for Kosovo (XK) — data, not code.

Sources:
- Law No. 06/L-010 on Notary (competencies, mandatory solemnization, art. 41)
- Administrative Instruction No. 02/2012 on provisional notary fees
  (Annex 1 value brackets + fixed fees per article)

The platform never performs notarization (the law requires physical presence
before a notary); it prepares citizens: which act they need, what documents
to bring, and roughly what it costs.
"""

# Annex 1 — fee by transaction value (EUR): (from, to, fee)
NOTARY_FEE_BRACKETS: list[tuple[float, float, int]] = [
    (0.01, 2_500.00, 20),
    (2_501.00, 5_000.00, 30),
    (5_001.00, 20_000.00, 50),
    (20_001.00, 60_000.00, 80),
    (60_001.00, 100_000.00, 120),
]
# Above 100 000 €: +20 € per started 20 000 €, total fee capped at 1 000 €.
NOTARY_FEE_OVER_STEP_EUR = 20
NOTARY_FEE_OVER_PER_EUR = 20_000
NOTARY_FEE_CAP_EUR = 1_000
# Solemnization of a party-drafted document = 80% of the Annex 1 fee (art. 23)
SOLEMNIZATION_FACTOR = 0.8


def annex1_fee(value_eur: float) -> int:
    """Fee for a notarial act by transaction value (Annex 1 + art. 21.2)."""
    for lo, hi, fee in NOTARY_FEE_BRACKETS:
        if lo <= value_eur <= hi:
            return fee
    if value_eur > NOTARY_FEE_BRACKETS[-1][1]:
        import math

        over = value_eur - NOTARY_FEE_BRACKETS[-1][1]
        fee = NOTARY_FEE_BRACKETS[-1][2] + NOTARY_FEE_OVER_STEP_EUR * math.ceil(
            over / NOTARY_FEE_OVER_PER_EUR
        )
        return min(fee, NOTARY_FEE_CAP_EUR)
    return NOTARY_FEE_BRACKETS[0][2]


# Common notarial matters citizens ask about. act_type: "akt" (notarial act),
# "solemnizim" (party-drafted, notary solemnizes — 80% of Annex 1),
# "vertetim" (certification, fixed small fees). fee: {"annex1"|"fixed":N|
# "solemnizim"} — how the estimate is computed. checklist keys are localized
# on the frontend via the labels below.
NOTARY_ACTS: list[dict] = [
    {
        "code": "prone_shitblerje",
        "act_type": "akt",
        "fee": "annex1",
        "value_based": True,
        "name": {
            "sq": "Kontratë për shitblerje të paluajtshmërisë (shtëpi, banesë, tokë)",
            "sr": "Ugovor o kupoprodaji nepokretnosti (kuća, stan, zemljište)",
            "tr": "Taşınmaz satış sözleşmesi (ev, daire, arsa)",
            "bs": "Ugovor o kupoprodaji nekretnine (kuća, stan, zemljište)",
            "en": "Real-estate sale contract (house, apartment, land)",
            "zh": "不动产买卖合同（房屋、公寓、土地）",
        },
        "checklist": [
            "ids_both", "property_certificate", "cadastre_copy",
            "tax_clearance", "spouse_consent",
        ],
    },
    {
        "code": "marreveshje_bashkeshortore",
        "act_type": "solemnizim",
        "fee": "solemnizim",
        "value_based": True,
        "mandatory_solemnization": True,
        "name": {
            "sq": "Marrëveshje pasurore mes bashkëshortëve",
            "sr": "Imovinski sporazum između supružnika",
            "tr": "Eşler arası mal rejimi sözleşmesi",
            "bs": "Imovinski sporazum između supružnika",
            "en": "Spousal property agreement",
            "zh": "夫妻财产协议",
        },
        "checklist": ["ids_both", "marriage_certificate", "property_certificate"],
    },
    {
        "code": "testament",
        "act_type": "akt",
        "fee": {"fixed": 50},
        "value_based": False,
        "name": {
            "sq": "Testament noterial",
            "sr": "Notarski testament",
            "tr": "Noter vasiyetnamesi",
            "bs": "Notarski testament",
            "en": "Notarial will (testament)",
            "zh": "公证遗嘱",
        },
        "checklist": ["id_own", "property_certificate", "heirs_data"],
    },
    {
        "code": "trashegimi",
        "act_type": "akt",
        "fee": "annex1",
        "value_based": True,
        "name": {
            "sq": "Procedura e trashëgimisë jokontestimore",
            "sr": "Ostavinski postupak (vanparnični)",
            "tr": "Çekişmesiz miras işlemi",
            "bs": "Ostavinski postupak (vanparnični)",
            "en": "Non-contentious inheritance procedure",
            "zh": "非争议继承程序",
        },
        "checklist": [
            "death_certificate", "family_certificate", "ids_heirs",
            "property_certificate", "bank_statements",
        ],
    },
    {
        "code": "autorizim_noterial",
        "act_type": "akt",
        "fee": {"fixed": 20},
        "value_based": False,
        "name": {
            "sq": "Autorizim/prokurë noteriale (p.sh. për shitje, përfaqësim)",
            "sr": "Notarsko punomoćje (npr. za prodaju, zastupanje)",
            "tr": "Noter vekaletnamesi (örn. satış, temsil)",
            "bs": "Notarska punomoć (npr. za prodaju, zastupanje)",
            "en": "Notarial power of attorney (e.g. for sale, representation)",
            "zh": "公证授权书（例如出售、代理）",
        },
        "checklist": ["id_own", "agent_data", "property_certificate_optional"],
    },
    {
        "code": "kontrate_veture",
        "act_type": "vertetim",
        "fee": "annex1",
        "value_based": True,
        "name": {
            "sq": "Kontratë për shitblerje të veturës",
            "sr": "Ugovor o kupoprodaji vozila",
            "tr": "Araç satış sözleşmesi",
            "bs": "Ugovor o kupoprodaji vozila",
            "en": "Vehicle sale contract",
            "zh": "车辆买卖合同",
        },
        "checklist": ["ids_both", "vehicle_registration"],
    },
    {
        "code": "themelim_biznesi",
        "act_type": "akt",
        "fee": {"fixed": 100},
        "value_based": False,
        "name": {
            "sq": "Akt themelues i shoqërisë tregtare",
            "sr": "Osnivački akt privrednog društva",
            "tr": "Şirket kuruluş senedi",
            "bs": "Osnivački akt privrednog društva",
            "en": "Company founding act",
            "zh": "公司设立文件",
        },
        "checklist": ["ids_founders", "business_name", "activity_data"],
    },
    {
        "code": "vertetim_nenshkrimi",
        "act_type": "vertetim",
        "fee": {"fixed": 1},
        "value_based": False,
        "per_unit": "signature_page",
        "name": {
            "sq": "Vërtetim i nënshkrimit",
            "sr": "Overa potpisa",
            "tr": "İmza tasdiki",
            "bs": "Ovjera potpisa",
            "en": "Signature certification",
            "zh": "签名认证",
        },
        "checklist": ["id_own", "document_to_sign"],
    },
    {
        "code": "vertetim_kopje",
        "act_type": "vertetim",
        "fee": {"fixed": 1},
        "value_based": False,
        "per_unit": "page",
        "name": {
            "sq": "Vërtetim i kopjes së dokumentit",
            "sr": "Overa kopije dokumenta",
            "tr": "Belge sureti tasdiki",
            "bs": "Ovjera kopije dokumenta",
            "en": "Certified copy of a document",
            "zh": "文件副本认证",
        },
        "checklist": ["original_document"],
    },
]

# Checklist item labels (×6 locales) used by NOTARY_ACTS.checklist.
NOTARY_CHECKLIST_LABELS: dict[str, dict[str, str]] = {
    "ids_both": {
        "sq": "Letërnjoftimet e të dyja palëve",
        "sr": "Lične karte obe strane", "tr": "Her iki tarafın kimlikleri",
        "bs": "Lične karte obje strane", "en": "ID cards of both parties",
        "zh": "双方身份证",
    },
    "id_own": {
        "sq": "Letërnjoftimi yt",
        "sr": "Vaša lična karta", "tr": "Kimliğiniz",
        "bs": "Vaša lična karta", "en": "Your ID card", "zh": "您的身份证",
    },
    "ids_heirs": {
        "sq": "Letërnjoftimet e të gjithë trashëgimtarëve",
        "sr": "Lične karte svih naslednika", "tr": "Tüm mirasçıların kimlikleri",
        "bs": "Lične karte svih nasljednika", "en": "ID cards of all heirs",
        "zh": "所有继承人的身份证",
    },
    "ids_founders": {
        "sq": "Letërnjoftimet e themeluesve",
        "sr": "Lične karte osnivača", "tr": "Kurucuların kimlikleri",
        "bs": "Lične karte osnivača", "en": "Founders' ID cards",
        "zh": "创始人身份证",
    },
    "property_certificate": {
        "sq": "Certifikata e pronësisë (nga kadastra/komuna)",
        "sr": "List nepokretnosti (katastar/opština)",
        "tr": "Mülkiyet belgesi (kadastro/belediye)",
        "bs": "List nepokretnosti (katastar/opština)",
        "en": "Property ownership certificate (cadastre/municipality)",
        "zh": "不动产权属证书（地籍/市政）",
    },
    "property_certificate_optional": {
        "sq": "Certifikata e pronësisë (nëse autorizimi ka të bëjë me pronë)",
        "sr": "List nepokretnosti (ako se punomoćje odnosi na imovinu)",
        "tr": "Mülkiyet belgesi (vekalet mülkle ilgiliyse)",
        "bs": "List nepokretnosti (ako se punomoć odnosi na imovinu)",
        "en": "Property certificate (if the authorization concerns property)",
        "zh": "权属证书（如授权涉及财产）",
    },
    "cadastre_copy": {
        "sq": "Kopja e planit kadastral",
        "sr": "Kopija katastarskog plana", "tr": "Kadastro planı kopyası",
        "bs": "Kopija katastarskog plana", "en": "Cadastral plan copy",
        "zh": "地籍图副本",
    },
    "tax_clearance": {
        "sq": "Vërtetimi i pagesës së tatimit në pronë",
        "sr": "Potvrda o plaćenom porezu na imovinu",
        "tr": "Emlak vergisi ödeme belgesi",
        "bs": "Potvrda o plaćenom porezu na imovinu",
        "en": "Property tax clearance certificate", "zh": "房产税完税证明",
    },
    "spouse_consent": {
        "sq": "Pëlqimi i bashkëshortit/es (nëse prona është e përbashkët)",
        "sr": "Saglasnost supružnika (ako je imovina zajednička)",
        "tr": "Eş muvafakati (mülk ortaksa)",
        "bs": "Saglasnost supružnika (ako je imovina zajednička)",
        "en": "Spouse's consent (if the property is joint)",
        "zh": "配偶同意书（如为共同财产）",
    },
    "marriage_certificate": {
        "sq": "Certifikata e martesës",
        "sr": "Izvod iz matične knjige venčanih", "tr": "Evlilik cüzdanı",
        "bs": "Izvod iz matične knjige vjenčanih", "en": "Marriage certificate",
        "zh": "结婚证",
    },
    "death_certificate": {
        "sq": "Certifikata e vdekjes së trashëgimlënësit",
        "sr": "Izvod iz matične knjige umrlih ostavioca",
        "tr": "Miras bırakanın ölüm belgesi",
        "bs": "Izvod iz matične knjige umrlih ostavioca",
        "en": "Deceased's death certificate", "zh": "被继承人死亡证明",
    },
    "family_certificate": {
        "sq": "Certifikata familjare / e trungut familjar",
        "sr": "Porodični list", "tr": "Aile nüfus kaydı",
        "bs": "Porodični list", "en": "Family status certificate",
        "zh": "家庭关系证明",
    },
    "heirs_data": {
        "sq": "Të dhënat e trashëgimtarëve që dëshiron t'i përfshish",
        "sr": "Podaci naslednika koje želite obuhvatiti",
        "tr": "Dahil etmek istediğiniz mirasçıların bilgileri",
        "bs": "Podaci nasljednika koje želite obuhvatiti",
        "en": "Details of the heirs you want to include", "zh": "拟列入继承人的信息",
    },
    "bank_statements": {
        "sq": "Të dhënat për llogaritë bankare/kursimet e trashëgimlënësit",
        "sr": "Podaci o bankovnim računima/štednji ostavioca",
        "tr": "Miras bırakanın banka hesap bilgileri",
        "bs": "Podaci o bankovnim računima/štednji ostavioca",
        "en": "Deceased's bank account/savings details", "zh": "被继承人银行账户信息",
    },
    "agent_data": {
        "sq": "Të dhënat e personit që autorizon (emri, numri personal)",
        "sr": "Podaci ovlašćenog lica (ime, lični broj)",
        "tr": "Yetkilendirilen kişinin bilgileri (ad, kimlik no)",
        "bs": "Podaci ovlaštene osobe (ime, lični broj)",
        "en": "Authorized person's details (name, personal number)",
        "zh": "被授权人信息（姓名、身份证号）",
    },
    "vehicle_registration": {
        "sq": "Libreza e veturës",
        "sr": "Saobraćajna dozvola vozila", "tr": "Araç ruhsatı",
        "bs": "Saobraćajna dozvola vozila", "en": "Vehicle registration card",
        "zh": "车辆行驶证",
    },
    "business_name": {
        "sq": "Emri i propozuar i biznesit dhe adresa",
        "sr": "Predloženi naziv firme i adresa",
        "tr": "Önerilen işletme adı ve adresi",
        "bs": "Predloženi naziv firme i adresa",
        "en": "Proposed business name and address", "zh": "拟用商号及地址",
    },
    "activity_data": {
        "sq": "Veprimtaria dhe pjesët e themeluesve",
        "sr": "Delatnost i udeli osnivača", "tr": "Faaliyet ve kurucu payları",
        "bs": "Djelatnost i udjeli osnivača",
        "en": "Business activity and founders' shares", "zh": "经营范围及创始人份额",
    },
    "original_document": {
        "sq": "Dokumenti origjinal që do të kopjohet",
        "sr": "Originalni dokument koji se kopira",
        "tr": "Kopyalanacak orijinal belge",
        "bs": "Originalni dokument koji se kopira",
        "en": "The original document to be copied", "zh": "待复印的原件",
    },
    "document_to_sign": {
        "sq": "Dokumenti që do të nënshkruhet (i pa nënshkruar — nënshkruhet para noterit)",
        "sr": "Dokument koji se potpisuje (nepotpisan — potpisuje se pred notarom)",
        "tr": "İmzalanacak belge (imzasız — noter önünde imzalanır)",
        "bs": "Dokument koji se potpisuje (nepotpisan — potpisuje se pred notarom)",
        "en": "The document to sign (unsigned — you sign before the notary)",
        "zh": "待签署文件（未签名——在公证人面前签署）",
    },
}
