// Curated public "udhëzues" articles for the Kosovo market (D-048): the ten
// most-asked legal questions of citizens, written in Albanian as general
// information (not individual legal advice), each with a CTA toward Ava /
// posto-rastin. Static data, same shape as the German Ratgeber articles;
// content reviewed against the cited Kosovo statutes as of 2026-08.

import type { RatgeberArticle } from "@/lib/ratgeber";

const XK_ARTICLES: Omit<RatgeberArticle, "country">[] = [
  {
    slug: "largimi-nga-puna",
    area: "E drejta e punës",
    title: "Largimi nga puna: të drejtat tuaja dhe afati 30-ditor",
    description:
      "Largimi nga puna duhet të jetë me shkrim dhe i arsyetuar (Ligji i Punës Nr. 03/L-212). Kërkesa te punëdhënësi, Inspektorati i Punës dhe padia brenda 30 ditësh.",
    updated: "2026-08-01",
    facts: [
      "Largimi duhet të bëhet me shkrim dhe me arsyetim (Ligji i Punës, neni 70)",
      "Kërkesa për mbrojtjen e të drejtave te punëdhënësi: 15 ditë (neni 78)",
      "Kontesti i punës në gjykatë: 30 ditë nga shkelja ose vendimi (neni 79)",
    ],
    sections: [
      {
        h: "Kur është i ligjshëm largimi",
        p: [
          "Punëdhënësi mund ta ndërpresë kontratën e punës vetëm për arsyet e parapara në Ligjin e Punës Nr. 03/L-212: sjellje e rëndë ose përsëritje e shkeljeve, mosarritje e rezultateve të pritshme pas paralajmërimit, apo arsye ekonomike, teknike a organizative. Largimi duhet të jepet me shkrim, me arsyetim dhe me udhëzim për mjetin juridik.",
          "Ligji parasheh edhe afatin e njoftimit sipas kohëzgjatjes së punësimit — largimi «nga sot» pa afat njoftimi lejohet vetëm në rastet e rënda të parapara me ligj.",
        ],
      },
      {
        h: "Hapi i parë: kërkesa te punëdhënësi",
        p: [
          "Nëse vlerësoni se ju është shkelur e drejta, keni 15 ditë të kërkoni me shkrim nga punëdhënësi realizimin e saj (neni 78). Ruajeni një kopje me datë të pranimit — kjo kërkesë dokumenton se keni reaguar me kohë.",
          "Paralelisht mund t'i drejtoheni Inspektoratit të Punës, i cili mund të konstatojë shkeljet dhe të shqiptojë masa ndaj punëdhënësit.",
        ],
      },
      {
        h: "Padia brenda 30 ditësh",
        p: [
          "Kontestin e punës në gjykatën kompetente duhet ta filloni brenda 30 ditësh nga dita e dorëzimit të vendimit ose nga dita kur keni mësuar për shkeljen (neni 79). Ky afat është i shkurtër dhe humbja e tij zakonisht e mbyll rrugën gjyqësore — prandaj çdo ditë numërohet.",
          "Në gjykatë mund të kërkoni kthimin në punë ose kompensimin e pagave të humbura, si dhe pagat e papaguara, pushimin e pashfrytëzuar dhe kontributet pensionale të paderdhura.",
        ],
      },
      {
        h: "Çfarë të bëni menjëherë",
        p: [
          "Mblidhni kontratën e punës, vendimin e largimit, listat e pagave dhe çdo komunikim me shkrim. Mos nënshkruani deklarata se «nuk keni asnjë kërkesë» pa i kuptuar pasojat. Dhe kërkoni shpejt vlerësim të rastit — afati 30-ditor nuk pret.",
        ],
      },
    ],
  },
  {
    slug: "urdhri-permbarimor",
    area: "Përmbarimi",
    title: "Urdhër përmbarimor nga përmbaruesi: 7 ditë për prapësim",
    description:
      "Përmbaruesi privat nuk e shqyrton themelin e borxhit — pa prapësim brenda 7 ditësh urdhri bëhet i ekzekutueshëm (Ligji Nr. 04/L-139 për Procedurën Përmbarimore).",
    updated: "2026-08-01",
    facts: [
      "Prapësimi kundër urdhrit përmbarimor: 7 ditë nga dorëzimi (LPP, Ligji Nr. 04/L-139)",
      "Përmbaruesi nuk e verifikon vetë a është borxhi i drejtë — atë e bën gjykata pas prapësimit",
      "Edhe borxhet e parashkruara ekzekutohen nëse nuk kundërshtohen me kohë",
    ],
    sections: [
      {
        h: "Çfarë do të thotë urdhri përmbarimor",
        p: [
          "Bankat, operatorët telefonikë, komunat dhe kreditorë të tjerë i realizojnë borxhet përmes përmbaruesve privatë, në bazë të një «dokumenti autentik» (fatura, kontrata, pasqyra e llogarisë) ose të një vendimi gjyqësor. Përmbaruesi nuk e gjykon a është kërkesa e drejtë — ai vetëm e zbaton procedurën sipas Ligjit Nr. 04/L-139 për Procedurën Përmbarimore.",
          "Prandaj edhe kërkesa të pabaza, të llogaritura gabimisht ose të parashkruara mund të përfundojnë në ekzekutim, nëse nuk reagoni.",
        ],
      },
      {
        h: "Afati 7-ditor për prapësim",
        p: [
          "Nga dita kur ju dorëzohet urdhri, keni 7 ditë të paraqisni prapësim me shkrim. Në prapësim shënoni pse e kundërshtoni kërkesën: borxhi është paguar, shuma është e gabuar, kërkesa është parashkruar, apo dokumenti nuk ju përket juve.",
          "Prapësimi i paraqitur me kohë e ndal ekzekutimin e kërkesave nga dokumenti autentik dhe çështja kalon në gjykatë, ku kreditori duhet ta provojë borxhin si në çdo kontest tjetër.",
        ],
      },
      {
        h: "Nëse afati ka kaluar",
        p: [
          "Pas afatit fillon ekzekutimi: bllokimi i llogarisë bankare, ndalesa në pagë ose regjistrimi i barrës mbi pasuri. Edhe atëherë ka mjete juridike të kufizuara (p.sh. kërkesa për kthim në gjendjen e mëparshme nëse dorëzimi ka qenë i parregullt), por pozita juaj është shumë më e vështirë — prandaj mos e injoroni asnjë zarf nga përmbaruesi.",
          "Nëse borxhi është real, shpesh ia vlen të negocioni pagesë me këste me kreditorin ose përmbaruesin para se të rriten shpenzimet e procedurës.",
        ],
      },
    ],
  },
  {
    slug: "kontesti-i-qirase",
    area: "Qiraja",
    title: "Kontesti i qirasë: të drejtat e qiramarrësit dhe të qiradhënësit",
    description:
      "Kontrata e qirasë rregullohet nga Ligji për Marrëdhëniet e Detyrimeve (Nr. 04/L-077): të metat e banesës, ngritja e qirasë, ndërprerja dhe dëbimi — çfarë vlen në Kosovë.",
    updated: "2026-08-01",
    facts: [
      "Qiraja rregullohet nga LMD (Ligji Nr. 04/L-077) dhe nga vetë kontrata",
      "Qiradhënësi përgjigjet për të metat që e pengojnë përdorimin e banesës",
      "Ndërprerja bëhet sipas kontratës — pa vendim gjyqësor s'ka dëbim të dhunshëm",
    ],
    sections: [
      {
        h: "Kontrata është ligji i palëve",
        p: [
          "Në Kosovë nuk ka ligj të veçantë për qiratë e banesave — marrëdhënia rregullohet nga kontrata dhe nga dispozitat e qirasë në Ligjin Nr. 04/L-077 për Marrëdhëniet e Detyrimeve (LMD). Prandaj kontrata me shkrim është mbrojtja juaj kryesore: shuma, afati, depozita, kush i paguan riparimet dhe si ndërpritet marrëdhënia.",
          "Edhe qiraja gojore është e vlefshme, por pa dokument bëhet fjalë kundër fjale — insistoni në kontratë me shkrim dhe në dëshmi pagese (transfer bankar, jo para në dorë pa faturë).",
        ],
      },
      {
        h: "Të metat dhe riparimet",
        p: [
          "Qiradhënësi detyrohet ta dorëzojë dhe ta mbajë banesën në gjendje të përdorshme. Për të meta që e pengojnë përdorimin (lagështia, ngrohja që s'punon, rrjedhjet), njoftojeni me shkrim dhe caktoni afat për riparim. Sipas LMD-së, mund të kërkoni ulje të qirasë për periudhën e së metës, e në raste të rënda ta ndërprisni kontratën.",
          "Riparimet e vogla të përdorimit të përditshëm zakonisht i bart qiramarrësi — shikoni çfarë thotë kontrata juaj.",
        ],
      },
      {
        h: "Ndërprerja dhe dëbimi",
        p: [
          "Ndërprerja bëhet sipas afateve të kontratës; për kontratat pa afat vlejnë afatet e njoftimit sipas LMD-së. Qiradhënësi nuk ka të drejtë t'ju ndërrojë bravën, t'ju ndërpresë rrymën apo t'ju nxjerrë me forcë — dëbimi bëhet vetëm me vendim gjyqësor dhe përmes procedurës përmbarimore.",
          "Nëse qiramarrësi nuk paguan, qiradhënësi duhet ta ndërpresë kontratën me shkrim dhe të kërkojë lirimin e banesës e pagesën e borxhit në gjykatë — vetëgjyqësia i kthehet kundër atij që e ushtron.",
        ],
      },
    ],
  },
  {
    slug: "kthimi-i-depozites",
    area: "Qiraja",
    title: "Kthimi i depozitës së qirasë: si ta merrni mbrapa",
    description:
      "Depozita është sigurim, jo dhuratë: pas dorëzimit të banesës pa dëme e pa borxhe, qiradhënësi duhet ta kthejë. Si të dokumentoheni dhe si ta kërkoni në gjykatë.",
    updated: "2026-08-01",
    facts: [
      "Depozita kthehet kur banesa dorëzohet pa dëme dhe pa qira a shpenzime të papaguara",
      "Amortizimi normal i banesës nuk zbritet nga depozita",
      "Procesverbali me foto në hyrje dhe në dalje është dëshmia vendimtare",
    ],
    sections: [
      {
        h: "Për çfarë shërben depozita",
        p: [
          "Depozita (zakonisht një ose dy qira mujore) e siguron qiradhënësin për qira të papaguara, shpenzime dhe dëme përtej përdorimit normal. Ajo mbetet pasuri e qiramarrësit: kur marrëdhënia përfundon dhe banesa dorëzohet në rregull, depozita kthehet e plotë.",
        ],
      },
      {
        h: "Çfarë lejohet të zbritet — dhe çfarë jo",
        p: [
          "Zbriten qiratë dhe faturat e papaguara dhe dëmet e shkaktuara nga qiramarrësi (dera e thyer, njollat nga pakujdesia). Nuk zbritet konsumimi normal: muret që kanë nevojë për lyerje pas disa vitesh, mobiliet e vjetruara nga përdorimi i zakonshëm apo pajisjet që prishen nga vjetërsia.",
          "Kërkojini qiradhënësit llogari të specifikuar për çdo zbritje — «po e mbaj depozitën» pa arsyetim nuk është bazë ligjore.",
        ],
      },
      {
        h: "Si të siguroheni që në fillim",
        p: [
          "Në hyrje bëni procesverbal pranim-dorëzimi me foto të çdo hapësire dhe listë të mobilieve, të nënshkruar nga të dyja palët; përsëriteni të njëjtën në dalje. Paguajeni depozitën me transfer bankar me përshkrim «depozitë qiraje», që të keni gjurmë.",
        ],
      },
      {
        h: "Nëse qiradhënësi nuk e kthen",
        p: [
          "Dërgojini kërkesë me shkrim me afat (p.sh. 15 ditë) dhe paralajmërim se do t'i drejtoheni gjykatës. Pastaj mund të parashtroni padi për kthimin e depozitës me kamatëvonesë — për shuma të tilla procedura zhvillohet si kontest i vlerës së vogël dhe procesverbali me foto e bën provën tuaj kryesore.",
        ],
      },
    ],
  },
  {
    slug: "trashegimia",
    area: "Trashëgimia",
    title: "Trashëgimia në Kosovë: radhët, testamenti dhe procedura te noteri",
    description:
      "Kush trashëgon sipas Ligjit Nr. 2004/26 për Trashëgiminë: radhët e trashëgimtarëve, pjesa e domosdoshme, heqja dorë dhe procedura trashëgimore te noteri.",
    updated: "2026-08-01",
    facts: [
      "Radha e parë: fëmijët dhe bashkëshorti/ja — në pjesë të barabarta (Ligji Nr. 2004/26)",
      "Testamenti mund ta ndryshojë ndarjen, por jo pjesën e domosdoshme të të afërmve",
      "Procedura trashëgimore (jokontestimore) zhvillohet te noteri",
    ],
    sections: [
      {
        h: "Kush trashëgon kur s'ka testament",
        p: [
          "Sipas Ligjit Nr. 2004/26 për Trashëgiminë, trashëgimia ligjore ndahet sipas radhëve: në radhën e parë trashëgojnë fëmijët dhe bashkëshorti/ja e të ndjerit në pjesë të barabarta; nëse s'ka pasardhës, vijnë prindërit dhe bashkëshorti/ja, e pastaj të afërmit e radhëve të mëtejme. Vajzat dhe djemtë trashëgojnë njësoj — heqja dorë «tradicionale» e motrave në favor të vëllezërve është e vlefshme vetëm nëse jepet lirisht në procedurë, dhe askush s'mund të detyrohet për të.",
        ],
      },
      {
        h: "Testamenti dhe pjesa e domosdoshme",
        p: [
          "Me testament (i shkruar dorazi, para dëshmitarëve ose te noteri) trashëgimlënësi mund ta ndajë pasurinë ndryshe. Kufiri është pjesa e domosdoshme: pasardhësit, bashkëshorti/ja dhe në raste të caktuara prindërit kanë të drejtë në një pjesë të garantuar të asaj që do t'u takonte sipas ligjit, të cilën mund ta kërkojnë edhe kundër testamentit.",
        ],
      },
      {
        h: "Procedura: te noteri, jo domosdo në gjykatë",
        p: [
          "Procedura trashëgimore në Kosovë zhvillohet si procedurë jokontestimore te noteri: shpallet vdekja, identifikohen trashëgimtarët dhe pasuria, dhe noteri nxjerr aktvendimin mbi trashëgiminë, me të cilin bëhet bartja në kadastër e në banka. Nëse trashëgimtarët nuk pajtohen (p.sh. kontestohet testamenti ose përbërja e pasurisë), çështja kontestuese kalon në gjykatë.",
          "Trashëgimia mund edhe të refuzohet — kjo ka rëndësi kur i ndjeri ka lënë borxhe, sepse trashëgimtari përgjigjet për to deri në vlerën e pasurisë së trashëguar.",
        ],
      },
    ],
  },
  {
    slug: "divorci-dhe-alimentacioni",
    area: "E drejta familjare",
    title: "Divorci dhe alimentacioni: procedura, kujdestaria, pasuria",
    description:
      "Shkurorëzimi sipas Ligjit për Familjen (Nr. 2004/32): me marrëveshje ose me padi, kujdestaria sipas interesit të fëmijës, alimentacioni dhe ndarja e pasurisë së përbashkët.",
    updated: "2026-08-01",
    facts: [
      "Shkurorëzimi: me propozim të përbashkët ose me padi (Ligji për Familjen Nr. 2004/32)",
      "Kujdestaria vendoset sipas interesit më të mirë të fëmijës, me mendimin e Qendrës për Punë Sociale",
      "Alimentacioni caktohet sipas nevojave të fëmijës dhe mundësive të prindit",
    ],
    sections: [
      {
        h: "Dy rrugët e shkurorëzimit",
        p: [
          "Ligji për Familjen i Kosovës Nr. 2004/32 njeh shkurorëzimin me propozim të përbashkët — kur bashkëshortët pajtohen për ndarjen, fëmijët dhe pasurinë, procedura është dukshëm më e shpejtë — dhe shkurorëzimin me padi, kur njëra palë kërkon zgjidhjen e martesës për shkak të çrregullimit serioz të marrëdhënieve. Gjykata zakonisht tenton edhe pajtimin, sidomos kur ka fëmijë të mitur.",
        ],
      },
      {
        h: "Fëmijët: kujdestaria dhe kontakti",
        p: [
          "Për besimin e fëmijës vendos gjykata sipas interesit më të mirë të fëmijës, me mendimin e Qendrës për Punë Sociale; mosha, lidhja emocionale dhe kushtet e secilit prind vlerësohen rast pas rasti. Prindi tjetër ka të drejtë dhe detyrë kontakti të rregullt — pengimi i kontaktit është shkelje që mund të ndryshojë vendimin për kujdestarinë.",
        ],
      },
      {
        h: "Alimentacioni",
        p: [
          "Prindi që nuk jeton me fëmijën detyrohet të kontribuojë për ushqimin (alimentacionin) sipas nevojave të fëmijës dhe mundësive të veta — gjykata merr parasysh të ardhurat, kushtet e banimit dhe detyrimet e tjera. Alimentacioni mund të ndryshohet kur ndryshojnë rrethanat, dhe mospagesa e tij është vepër penale e ndjekshme.",
          "Edhe bashkëshorti/ja pa mjete jetese mund të kërkojë ushqim nga tjetri për një periudhë, nëse plotësohen kushtet ligjore.",
        ],
      },
      {
        h: "Pasuria e përbashkët",
        p: [
          "Pasuria e fituar me punë gjatë martesës është pasuri e përbashkët dhe në ndarje secili bashkëshort merr pjesën sipas kontributit, ku vlerësohet edhe puna në shtëpi dhe kujdesi për fëmijët — jo vetëm të ardhurat. Pasuria e sjellë në martesë ose e fituar me trashëgimi a dhuratë mbetet e veçantë.",
        ],
      },
    ],
  },
  {
    slug: "aksidenti-i-trafikut",
    area: "Trafiku",
    title: "Aksidenti i trafikut: si ta merrni dëmshpërblimin",
    description:
      "Pas aksidentit pa fajin tuaj paguan siguruesi i palës përgjegjëse (Ligji Nr. 04/L-018). Procesverbali, kërkesa te siguruesi, Byroja Kosovare e Sigurimit dhe afatet.",
    updated: "2026-08-01",
    facts: [
      "Dëmin e paguan siguruesi i autopërgjegjësisë së shkaktarit (Ligji Nr. 04/L-018)",
      "Për automjete të pasiguruara ose të panjohura përgjigjet Byroja Kosovare e Sigurimit",
      "Kërkesa e dëmit parashkruhet — mos e lini me vite; siguruesi duhet të përgjigjet brenda 60 ditësh",
    ],
    sections: [
      {
        h: "Në vendin e aksidentit",
        p: [
          "Siguroni vendin, thirrni policinë kur ka lëndime ose dëm më të madh dhe fotografoni gjithçka: pozicionet e automjeteve, targat, gjurmët, dëmet. Për përplasje të vogla pa lëndime mund të plotësohet raporti evropian i aksidentit — nënshkruajeni vetëm nëse pajtoheni me përshkrimin. Mos pranoni faj «sa për t'u kry» dhe shënoni dëshmitarët.",
        ],
      },
      {
        h: "Kërkesa te siguruesi",
        p: [
          "Sipas Ligjit Nr. 04/L-018 për Sigurimin e Detyrueshëm nga Autopërgjegjësia, kërkesën për dëmshpërblim e paraqisni te siguruesi i automjetit që e ka shkaktuar aksidentin. Bashkëngjitni raportin e policisë ose raportin evropian, fotot, faturat e riparimit a ofertat, dhe për lëndime dokumentacionin mjekësor. Siguruesi detyrohet të përgjigjet me ofertë të arsyetuar ose refuzim të arsyetuar brenda 60 ditësh.",
          "Kompensohet dëmi material (riparimi, zhvlerësimi, automjeti zëvendësues kur arsyetohet) dhe dëmi jomaterial për lëndime: dhimbjet fizike, frika, zvogëlimi i aftësisë jetësore.",
        ],
      },
      {
        h: "Automjet i pasiguruar ose i panjohur",
        p: [
          "Nëse shkaktari ka ikur ose s'ka sigurim, kërkesa paraqitet te Byroja Kosovare e Sigurimit (BKS), e cila paguan nga fondi i garancisë sipas kushteve ligjore. Edhe aksidentet me automjete me targa të huaja trajtohen përmes sistemit të kartonit të gjelbër — mos hiqni dorë vetëm pse shkaktari s'është nga Kosova.",
        ],
      },
      {
        h: "Kur oferta është e ulët",
        p: [
          "Siguruesit shpesh ofrojnë shuma minimale, sidomos për dëmin jomaterial. Nuk jeni të detyruar ta pranoni ofertën e parë: kërkesa mund të negociohet dhe, në mungesë pajtimi, të parashtrohet padi ku dëmin e vlerëson eksperti gjyqësor. Kini kujdes afatet e parashkrimit sipas LMD-së — sa më herët të veproni, aq më e fortë është pozita juaj.",
        ],
      },
    ],
  },
  {
    slug: "ankesa-administrative",
    area: "E drejta administrative",
    title: "Ankesa kundër vendimit administrativ: nga ankesa te padia",
    description:
      "Kur komuna, ATK ose një organ tjetër ju refuzon një kërkesë, keni ankesë sipas LPPA-së (Nr. 05/L-031) dhe pastaj padi në konflikt administrativ brenda 30 ditësh.",
    updated: "2026-08-01",
    facts: [
      "Çdo vendim duhet të përmbajë udhëzimin juridik: ku dhe brenda sa ditësh ankoheni",
      "Ankesa te organi i shkallës së dytë sipas LPPA-së (Ligji Nr. 05/L-031)",
      "Padia në konflikt administrativ: 30 ditë nga vendimi përfundimtar (Ligji Nr. 03/L-202, neni 27)",
    ],
    sections: [
      {
        h: "Lexojeni udhëzimin juridik",
        p: [
          "Çdo akt administrativ — leje ndërtimi, vendim tatimor, refuzim i një kërkese në komunë — duhet të përmbajë udhëzimin juridik: cilit organ i drejtohet ankesa dhe brenda cilit afat. Afati i ankesës është i shkurtër (sipas Ligjit Nr. 05/L-031 për Procedurën e Përgjithshme Administrative dhe ligjeve të veçanta), prandaj reagoni menjëherë sapo ta pranoni vendimin.",
          "Nëse organi nuk vendos fare brenda afatit ligjor («heshtja administrative»), kjo trajtohet si refuzim dhe ju hap rrugën e mjeteve juridike.",
        ],
      },
      {
        h: "Ankesa në shkallën e dytë",
        p: [
          "Ankesa paraqitet me shkrim te organi që e ka nxjerrë vendimin ose te organi i shkallës së dytë, sipas udhëzimit. Shkruani qartë çfarë kontestoni: gjendjen faktike të vërtetuar gabimisht, zbatimin e gabuar të ligjit ose shkeljet e procedurës — dhe bashkëngjitni provat. Ankesa e paraqitur me kohë zakonisht e pezullon ekzekutimin e vendimit.",
        ],
      },
      {
        h: "Padia në konflikt administrativ",
        p: [
          "Kur ankesa refuzohet ose organi hesht, mund të parashtroni padi në Departamentin për Çështje Administrative brenda 30 ditësh nga dorëzimi i vendimit përfundimtar (Ligji Nr. 03/L-202 për Konfliktet Administrative, neni 27). Gjykata e shqyrton ligjshmërinë e aktit dhe mund ta anulojë e ta kthejë çështjen në rivendosje.",
          "Ruani çdo dokument me datë pranimi — afatet në të drejtën administrative llogariten nga dorëzimi, dhe dëshmia e datës shpesh e vendos fatin e rastit.",
        ],
      },
    ],
  },
  {
    slug: "parashkrimi-i-borxheve",
    area: "Detyrimet",
    title: "Parashkrimi i borxheve: kur një borxh nuk mund të kërkohet më",
    description:
      "Sipas LMD-së (Nr. 04/L-077) kërkesat parashkruhen me kalimin e kohës: 10 vjet afati i përgjithshëm, 3 vjet për kërkesat periodike dhe dëmet. Por parashkrimin duhet ta pretendoni vetë.",
    updated: "2026-08-01",
    facts: [
      "Afati i përgjithshëm i parashkrimit: 10 vjet (LMD, Ligji Nr. 04/L-077)",
      "Kërkesat periodike (qira, fatura, kamata) dhe dëmshpërblimi: afate më të shkurtra, si rregull 3 vjet",
      "Gjykata dhe përmbaruesi nuk kujdesen vetë për parashkrimin — duhet ta pretendoni ju",
    ],
    sections: [
      {
        h: "Si funksionon parashkrimi",
        p: [
          "Parashkrimi do të thotë se pas kalimit të afatit ligjor kreditori e humb të drejtën ta realizojë kërkesën me detyrim — borxhi nuk «fshihet», por debitori mund të refuzojë pagesën duke e pretenduar parashkrimin. Ligji Nr. 04/L-077 për Marrëdhëniet e Detyrimeve cakton afatin e përgjithshëm 10-vjeçar dhe afate më të shkurtra për lloje të caktuara kërkesash.",
        ],
      },
      {
        h: "Afatet që duhen ditur",
        p: [
          "Kërkesat periodike — qiraja, kamatat, faturat e shërbimeve që maturohen çdo muaj — parashkruhen si rregull për 3 vjet nga maturimi i secilës këste, e disa kërkesa (p.sh. ato komunale ndaj konsumatorëve) edhe më shpejt. Kërkesa e dëmshpërblimit parashkruhet 3 vjet nga dita kur e keni mësuar dëmin dhe shkaktarin, e më së largu brenda afatit absolut ligjor. Kërkesat e vërtetuara me vendim të formës së prerë kanë afat të gjatë, 10-vjeçar.",
          "Parashkrimi ndërpritet me pranimin e borxhit (pagesë e pjesshme, nënshkrim marrëveshjeje) dhe me padi a propozim përmbarimi — pas ndërprerjes afati fillon nga e para. Vërejtja e thjeshtë me telefon nga call-center-i nuk e ndërpret parashkrimin.",
        ],
      },
      {
        h: "Në praktikë: reagoni me prapësim",
        p: [
          "Kompanitë dhe agjencitë e arkëtimit shpesh kërkojnë përmes përmbaruesit edhe borxhe të vjetra të parashkruara. Meqë askush nuk e kontrollon parashkrimin sipas detyrës zyrtare, duhet ta pretendoni vetë — me prapësim brenda 7 ditësh kundër urdhrit përmbarimor ose si prapësim në kontest. Kujdes edhe me pagesat «e vogla sa për qetësi»: pagesa e pjesshme mund të trajtohet si pranim i borxhit dhe ta rikthejë afatin.",
        ],
      },
    ],
  },
  {
    slug: "puna-pa-kontrate",
    area: "E drejta e punës",
    title: "Puna pa kontratë: të drejtat tuaja edhe pa letër",
    description:
      "Kontrata me shkrim është detyrim i punëdhënësit (Ligji i Punës Nr. 03/L-212). Puna faktike krijon marrëdhënie pune — si t'i provoni dhe realizoni të drejtat tuaja.",
    updated: "2026-08-01",
    facts: [
      "Kontrata e punës lidhet me shkrim — detyrim i punëdhënësit (Ligji i Punës, neni 10)",
      "Edhe pa kontratë me shkrim, puna faktike krijon marrëdhënie pune me të gjitha të drejtat",
      "Inspektorati i Punës pranon ankesa dhe mund ta gjobisë punëdhënësin",
    ],
    sections: [
      {
        h: "Mungesa e kontratës është shkelje e punëdhënësit",
        p: [
          "Ligji i Punës Nr. 03/L-212 kërkon që kontrata e punës të lidhet me shkrim dhe të përmbajë elementet themelore: pagën, orarin, vendin e punës, kohëzgjatjen. Nëse punoni pa kontratë me shkrim, shkeljen e ka bërë punëdhënësi — jo ju — dhe kjo nuk jua heq të drejtat: marrëdhënia e punës ekziston nga vetë fakti që punoni me dijeninë e punëdhënësit.",
          "Pa kontratë me shkrim, marrëdhënia vlerësohet sipas kushteve reale të punës — përfshirë supozimin në favor të punëmarrësit për kohëzgjatjen e saj.",
        ],
      },
      {
        h: "Çfarë humbisni në praktikë",
        p: [
          "Puna «në të zezë» zakonisht do të thotë pa kontribute pensionale në Trust, pa sigurim nga aksidentet në punë, pa pushim të paguar dhe pa bazë për kredi a vizë. Në rast lëndimi në punë ose largimi të menjëhershëm, mungesa e dokumenteve e vështirëson — por nuk e pamundëson — mbrojtjen.",
        ],
      },
      {
        h: "Si ta provoni marrëdhënien e punës",
        p: [
          "Mblidhni gjithçka që dëshmon punën tuaj: mesazhet me urdhra pune, listat e ndërrimeve, pagesat bankare a fotografitë në vendin e punës, uniformën, dëshmitarët kolegë. Me këto prova mund t'i kërkoni në gjykatë pagat e papaguara, kontributet e paderdhura dhe të drejtat e tjera nga marrëdhënia e punës.",
        ],
      },
      {
        h: "Ku të drejtoheni",
        p: [
          "Ankesa te Inspektorati i Punës mund të bëhet edhe pa emër dhe mund të rezultojë me gjoba e me urdhër për lidhjen e kontratës. Për realizimin e pagave dhe kontributeve vendos gjykata — kini parasysh afatet e shkurtra të kontesteve të punës (kërkesa te punëdhënësi 15 ditë, padia 30 ditë nga shkelja), prandaj mos vononi.",
        ],
      },
    ],
  },
];

export const UDHEZUES_ARTICLES: RatgeberArticle[] = XK_ARTICLES.map((a) => ({
  ...a,
  country: "XK" as const,
}));

export function udhezuesBySlug(slug: string): RatgeberArticle | undefined {
  return UDHEZUES_ARTICLES.find((a) => a.slug === slug);
}
