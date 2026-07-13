# Drafte kontakti — rekrutimi i avokatëve të parë

> Përgatitur 2026-07-13 si pjesë e Fazës 2 të planit të përmirësimeve
> (pika 6: rekrutimi i avokatëve + shenja "Themelues").
> Këto janë drafte — pronari i redakton dhe i dërgon vetë.

## Konteksti

- Platforma ka tashmë kërkesë reale nga qytetarët (raste të postuara, pyetje
  për Ava-n), por asnjë avokat të verifikuar që i merr rastet.
- Shenja **"Themelues"** u jepet automatikisht 20 zyrave të para të verifikuara
  me OAK — përgjithmonë e dukshme në drejtorinë publike.
- Çdo avokat ka **kod referimi** te Cilësimet → "Fto një koleg"
  (`/regjistrohu?ref=KODI`) — baza e programit avokat-sjell-avokat.

---

## Draft 1 — Email për Odën e Avokatëve të Kosovës (OAK)

**Për:** [email zyrtar i OAK]
**Subjekti:** AvokatIM — platformë vendore që lidh qytetarët me avokatët e OAK-së

I/E nderuar,

Ju shkruaj për t'ju prezantuar **AvokatIM** (https://avokatiim.ai) — një
platformë e ndërtuar në Kosovë që lidh qytetarët me avokatët e licencuar
të OAK-së dhe u jep avokatëve një zyrë digjitale të plotë (lëndët, afatet
sipas LPK-së, dokumentet, faturimi, asistencë AI në gjuhën shqipe).

Pse mendoj se kjo është me interes për Odën:

1. **Qasja në drejtësi** — qytetarët marrin falas informim ligjor bazik
   (asistentja Ava mbi ligjet e Kosovës, me citime) dhe një kanal të thjeshtë
   për të gjetur avokat të verifikuar — përfshirë raste urgjente (SOS).
2. **Verifikimi përmes OAK-së** — në drejtorinë publike shfaqen vetëm
   avokatët me numër licence të verifikuar. Do të donim ta bënim këtë proces
   bashkë me Odën, që shenja e verifikimit të ketë peshë reale.
3. **Vendore dhe private** — të dhënat ruhen në Kosovë, dokumentet enkriptohen,
   dhe platforma është ndërtuar rreth ligjeve të Kosovës (LPK, afatet, tarifat).

Do të vlerësoja shumë një takim të shkurtër (edhe online) për t'jua
demonstruar platformën dhe për të diskutuar si mund të bashkëpunojmë —
p.sh. njoftim për anëtarët, verifikim i përbashkët i licencave, ose
thjesht reagimi juaj profesional.

Me respekt,
Arbër Arifi
[telefoni] · arifi.arber@gmail.com · https://avokatiim.ai

---

## Draft 2 — Email personal për avokaten e parë të regjistruar (Marigona Gashi)

**Për:** [email-i me të cilin u regjistrua]
**Subjekti:** Mirë se erdhe në AvokatIM — llogaria jote dhe shenja "Themelues"

E nderuar znj. Gashi,

Faleminderit që u regjistruat në AvokatIM — jeni ndër avokatët e parë në
platformë dhe kjo ka vlerë të veçantë për ne.

Vura re që llogaria juaj është krijuar, por profili publik ende nuk është
aktivizuar — pa të, qytetarët nuk mund t'ju gjejnë në drejtori dhe nuk
merrni raste nga tregu. Aktivizimi zgjat 2 minuta:

1. Kyçuni në https://avokatiim.ai/login
2. Hapni https://avokatiim.ai/onboarding (ose Cilësimet → Profili publik)
3. Aktivizoni dukshmërinë, shtoni fushat e praktikës dhe numrin e licencës
   së OAK-së — pas verifikimit merrni shenjën ✓ dhe, si një nga zyrat e para,
   shenjën e përhershme **"Themelues"**.

Gjatë 3 muajve të parë gjithçka është falas, pa kartelë dhe pa detyrime.
Nëse diçka nuk funksionon si prisni, ose keni sugjerime — më shkruani direkt
në këtë email; reagimi juaj formëson platformën.

Me respekt,
Arbër Arifi
Krijuesi i AvokatIM · https://avokatiim.ai

---

## Shënime për dërgimin

- OAK: gjej email-in zyrtar në https://oak-ks.org (sekretaria).
- Marigona Gashi: email-i i regjistrimit gjendet te Platforma → përdoruesit
  (llogaria e krijuar më 2026-07-11).
- Pas dërgimit: shëno përgjigjet këtu ose në JOURNAL, që agjentët e ardhshëm
  ta dinë statusin.

## Statusi

- **2026-07-13**: Email-i personal iu dërgua Marigona Gashit
  (marigonagashi.law@gmail.com) nga adresa e pronarit përmes SMTP
  (`backend/scripts/send_marigona_email.py`). Përmbajtja: hapat e mbetur të
  onboarding-ut (aktivizimi i profilit publik, fushat/qytetet, licenca OAK)
  dhe shenja "Themelues". Nudge-u automatik 48h u shënua si i dërguar
  (`profile_nudge_sent_at`) që të mos marrë email të dyfishtë.
  Përgjigja: në pritje.
