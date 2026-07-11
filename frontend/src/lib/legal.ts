// Public legal texts (ToS + Privacy Policy) in Kosovo's official languages
// plus extras. The authoritative long-form versions live in docs/legal/
// (Albanian); these are the user-facing summaries shown at /kushtet and
// /privatesia and linked from every consent checkbox.
import { Locale } from "./dictionaries";

export interface LegalSection {
  h: string;
  p: string;
}

export interface LegalDoc {
  title: string;
  updated: string;
  note: string;
  sections: LegalSection[];
}

const tosSq: LegalDoc = {
  title: "Kushtet e Përdorimit",
  updated: "Versioni 1.0 · Korrik 2026",
  note: "Teksti autoritativ është ai në gjuhën shqipe.",
  sections: [
    { h: "Shërbimi", p: "AvokatIM ofron menaxhim të lëndëve ligjore, afateve, dokumenteve, faturimit, komunikimit me klientë dhe asistencë me AI. Asistenca AI ka natyrë ndihmëse dhe nuk përbën këshillë ligjore — përgjegjësia profesionale mbetet e avokatit." },
    { h: "Llogaria", p: "Zyra përgjigjet për saktësinë e të dhënave të regjistrimit dhe ruajtjen e kredencialeve. Qasjet e paautorizuara raportohen menjëherë." },
    { h: "Të dhënat", p: "Të dhënat e lëndëve dhe dokumentet janë pronë e zyrës ligjore. Ato përpunohen vetëm sipas Marrëveshjes së Përpunimit të të Dhënave dhe Ligjit Nr. 06/L-082. Dokumentet ruhen të enkriptuara dhe indeksohen me modele lokale." },
    { h: "AI e jashtme", p: "Përdorimi i AI-së së jashtme është opsional dhe kontrollohet nga zyra në cilësimet; me çaktivizim përdoret vetëm modeli lokal që nuk dërgon asgjë jashtë serverit." },
    { h: "Detyrimet e përdoruesit", p: "Platforma nuk përdoret për qëllime të kundërligjshme dhe nuk ngarkohet përmbajtje e dëmshme. Zyra siguron bazë ligjore për të dhënat personale që fut në sistem." },
    { h: "Pagesa", p: "Çmimet publikohen veçmas. Pas kufizimit të llogarisë për mospagesë, të dhënat mbeten të eksportueshme për së paku 90 ditë." },
    { h: "Përgjegjësia", p: "Operatori nuk përgjigjet për vendimet profesionale të avokatit ose forcën madhore. Përgjegjësia maksimale kufizohet në shumën e paguar në 12 muajt e fundit." },
    { h: "E drejta e zbatueshme", p: "Zbatohet e drejta e Republikës së Kosovës; kontestet i zgjidh gjykata kompetente në Prishtinë. Ndryshimet njoftohen 30 ditë përpara." },
  ],
};

const tosSr: LegalDoc = {
  title: "Uslovi korišćenja",
  updated: "Verzija 1.0 · Jul 2026",
  note: "Merodavan je tekst na albanskom jeziku.",
  sections: [
    { h: "Usluga", p: "AvokatIM pruža upravljanje predmetima, rokovima, dokumentima, fakturisanjem, komunikacijom sa klijentima i AI asistenciju. AI pomoć je pomoćne prirode i ne predstavlja pravni savet — profesionalna odgovornost ostaje na advokatu." },
    { h: "Nalog", p: "Kancelarija odgovara za tačnost podataka pri registraciji i čuvanje kredencijala. Neovlašćeni pristupi se odmah prijavljuju." },
    { h: "Podaci", p: "Podaci predmeta i dokumenti su vlasništvo advokatske kancelarije. Obrađuju se isključivo prema Ugovoru o obradi podataka i Zakonu br. 06/L-082. Dokumenti se čuvaju šifrovani i indeksiraju lokalnim modelima." },
    { h: "Eksterna AI", p: "Korišćenje eksterne AI je opciono i kancelarija ga kontroliše u podešavanjima; kada je isključeno, koristi se samo lokalni model koji ništa ne šalje van servera." },
    { h: "Obaveze korisnika", p: "Platforma se ne koristi u nezakonite svrhe i ne otprema se štetan sadržaj. Kancelarija obezbeđuje pravni osnov za lične podatke koje unosi u sistem." },
    { h: "Plaćanje", p: "Cene se objavljuju posebno. Nakon ograničenja naloga zbog neplaćanja, podaci ostaju dostupni za izvoz najmanje 90 dana." },
    { h: "Odgovornost", p: "Operater ne odgovara za profesionalne odluke advokata ni za višu silu. Maksimalna odgovornost ograničena je na iznos plaćen u poslednjih 12 meseci." },
    { h: "Merodavno pravo", p: "Primenjuje se pravo Republike Kosovo; sporove rešava nadležni sud u Prištini. Izmene se najavljuju 30 dana unapred." },
  ],
};

const tosTr: LegalDoc = {
  title: "Kullanım Koşulları",
  updated: "Sürüm 1.0 · Temmuz 2026",
  note: "Bağlayıcı metin Arnavutça olandır.",
  sections: [
    { h: "Hizmet", p: "AvokatIM dava dosyaları, süreler, belgeler, faturalama, müvekkil iletişimi ve yapay zeka desteği sunar. AI yardımı destekleyici niteliktedir ve hukuki tavsiye değildir — mesleki sorumluluk avukata aittir." },
    { h: "Hesap", p: "Büro, kayıt bilgilerinin doğruluğundan ve kimlik bilgilerinin korunmasından sorumludur. Yetkisiz erişimler derhal bildirilir." },
    { h: "Veriler", p: "Dosya verileri ve belgeler hukuk bürosunun mülkiyetindedir. Yalnızca Veri İşleme Sözleşmesi ve 06/L-082 sayılı Kanun'a göre işlenir. Belgeler şifreli saklanır ve yerel modellerle dizinlenir." },
    { h: "Harici AI", p: "Harici AI kullanımı isteğe bağlıdır ve ayarlardan büro tarafından kontrol edilir; kapatıldığında sunucu dışına hiçbir şey göndermeyen yerel model kullanılır." },
    { h: "Kullanıcı yükümlülükleri", p: "Platform yasa dışı amaçlarla kullanılamaz ve zararlı içerik yüklenemez. Büro, sisteme girdiği kişisel veriler için hukuki dayanak sağlar." },
    { h: "Ödeme", p: "Fiyatlar ayrıca yayınlanır. Ödeme yapılmaması nedeniyle hesap kısıtlandıktan sonra veriler en az 90 gün dışa aktarılabilir kalır." },
    { h: "Sorumluluk", p: "Operatör, avukatın mesleki kararlarından veya mücbir sebepten sorumlu değildir. Azami sorumluluk son 12 ayda ödenen tutarla sınırlıdır." },
    { h: "Uygulanacak hukuk", p: "Kosova Cumhuriyeti hukuku uygulanır; uyuşmazlıkları Priştine'deki yetkili mahkeme çözer. Değişiklikler 30 gün önceden bildirilir." },
  ],
};

const tosBs: LegalDoc = {
  title: "Uslovi korištenja",
  updated: "Verzija 1.0 · Juli 2026",
  note: "Mjerodavan je tekst na albanskom jeziku.",
  sections: [
    { h: "Usluga", p: "AvokatIM pruža upravljanje predmetima, rokovima, dokumentima, fakturisanjem, komunikacijom s klijentima i AI asistenciju. AI pomoć je pomoćne prirode i ne predstavlja pravni savjet — profesionalna odgovornost ostaje na advokatu." },
    { h: "Račun", p: "Kancelarija odgovara za tačnost podataka pri registraciji i čuvanje kredencijala. Neovlašteni pristupi se odmah prijavljuju." },
    { h: "Podaci", p: "Podaci predmeta i dokumenti su vlasništvo advokatske kancelarije. Obrađuju se isključivo prema Ugovoru o obradi podataka i Zakonu br. 06/L-082. Dokumenti se čuvaju šifrirani i indeksiraju lokalnim modelima." },
    { h: "Eksterna AI", p: "Korištenje eksterne AI je opcionalno i kancelarija ga kontroliše u postavkama; kada je isključeno, koristi se samo lokalni model koji ništa ne šalje van servera." },
    { h: "Obaveze korisnika", p: "Platforma se ne koristi u nezakonite svrhe i ne učitava se štetan sadržaj. Kancelarija osigurava pravni osnov za lične podatke koje unosi u sistem." },
    { h: "Plaćanje", p: "Cijene se objavljuju posebno. Nakon ograničenja računa zbog neplaćanja, podaci ostaju dostupni za izvoz najmanje 90 dana." },
    { h: "Odgovornost", p: "Operater ne odgovara za profesionalne odluke advokata ni za višu silu. Maksimalna odgovornost ograničena je na iznos plaćen u posljednjih 12 mjeseci." },
    { h: "Mjerodavno pravo", p: "Primjenjuje se pravo Republike Kosovo; sporove rješava nadležni sud u Prištini. Izmjene se najavljuju 30 dana unaprijed." },
  ],
};

const tosEn: LegalDoc = {
  title: "Terms of Service",
  updated: "Version 1.0 · July 2026",
  note: "The authoritative text is the Albanian version.",
  sections: [
    { h: "The service", p: "AvokatIM provides legal matter management, deadlines, documents, billing, client communication and AI assistance. AI assistance is supportive in nature and is not legal advice — professional responsibility stays with the lawyer." },
    { h: "Account", p: "The firm is responsible for accurate registration data and for safeguarding member credentials. Unauthorized access must be reported immediately." },
    { h: "Data", p: "Matter data and documents are the property of the law firm. They are processed only under the Data Processing Agreement and Law No. 06/L-082. Documents are stored encrypted and indexed with local models." },
    { h: "External AI", p: "Use of external AI is optional and controlled by the firm in settings; when disabled, only the local model is used and nothing leaves the server." },
    { h: "User obligations", p: "The platform may not be used for unlawful purposes and no harmful content may be uploaded. The firm ensures a legal basis for the personal data it enters." },
    { h: "Payment", p: "Prices are published separately. After account restriction for non-payment, data remains exportable for at least 90 days." },
    { h: "Liability", p: "The operator is not liable for the lawyer's professional decisions or force majeure. Maximum liability is capped at the amount paid in the last 12 months." },
    { h: "Governing law", p: "The law of the Republic of Kosovo applies; disputes are resolved by the competent court in Pristina. Changes are announced 30 days in advance." },
  ],
};

const tosZh: LegalDoc = {
  title: "使用条款",
  updated: "版本 1.0 · 2026年7月",
  note: "以阿尔巴尼亚语文本为准。",
  sections: [
    { h: "服务", p: "AvokatIM 提供案件管理、期限、文件、计费、客户沟通和 AI 协助。AI 协助仅为辅助性质，不构成法律意见——职业责任仍由律师承担。" },
    { h: "账户", p: "律所负责注册信息的准确性并妥善保管成员凭据。发现未经授权的访问须立即报告。" },
    { h: "数据", p: "案件数据和文件归律所所有，仅根据数据处理协议和第06/L-082号法律处理。文件加密存储，并使用本地模型进行索引。" },
    { h: "外部 AI", p: "外部 AI 的使用是可选的，由律所在设置中控制；关闭后仅使用本地模型，任何内容都不会离开服务器。" },
    { h: "用户义务", p: "不得将平台用于非法目的，不得上传有害内容。律所须确保其录入的个人数据具有法律依据。" },
    { h: "付款", p: "价格另行公布。因未付款而受限后，数据在至少90天内仍可导出。" },
    { h: "责任", p: "运营方不对律师的职业决定或不可抗力负责。最高责任以最近12个月支付的金额为限。" },
    { h: "适用法律", p: "适用科索沃共和国法律；争议由普里什蒂纳有管辖权的法院解决。变更提前30天通知。" },
  ],
};

const privSq: LegalDoc = {
  title: "Politika e Privatësisë",
  updated: "Versioni 1.0 · Korrik 2026 · Sipas Ligjit Nr. 06/L-082",
  note: "Teksti autoritativ është ai në gjuhën shqipe.",
  sections: [
    { h: "Kush i përpunon të dhënat", p: "Kontrolluesi i të dhënave është zyra ligjore që ju përfaqëson. Operatori i AvokatIM është përpunues dhe vepron vetëm sipas udhëzimeve të zyrës dhe DPA-së." },
    { h: "Çfarë përpunohet", p: "Të dhëna identifikuese (emri, nr. personal, kontakti), të dhëna të lëndës (parashtresa, prova, korrespondenca), financiare (fatura, mjetet në besim) dhe teknike (log-e, IP, pëlqime)." },
    { h: "Si ruhen", p: "Dokumentet ruhen të enkriptuara. Indeksimi bëhet me modele lokale — teksti nuk dërgohet jashtë. Pagesat me kartelë përpunohen nga ofruesi i pagesave; të dhënat e kartelës nuk ruhen." },
    { h: "AI e jashtme", p: "Nëse zyra e aktivizon, fragmente pyetjesh dhe konteksti mund t'i dërgohen ofruesit të jashtëm të AI-së. Kjo shënohet qartë në asistente dhe mund të çaktivizohet plotësisht." },
    { h: "Të drejtat tuaja", p: "Qasje, korrigjim, fshirje (kur s'ka detyrim ligjor ruajtjeje), kufizim, bartje dhe tërheqje pëlqimi në çdo kohë. Kërkesat trajtohen brenda 30 ditësh. Ankesa: Agjencia për Informim dhe Privatësi (AIP)." },
    { h: "Ruajtja", p: "Dosjet ruhen aq sa e kërkojnë detyrimet profesionale, tatimore dhe AML. Pas afatit, lëndët shënjohen për shqyrtim dhe vendos avokati." },
    { h: "Transferimet ndërkombëtare", p: "Disa nënpërpunues opsionalë ndodhen jashtë Kosovës (AI e jashtme, pagesat, email-i). Lista e plotë me masat mbrojtëse mbahet në aneksin e DPA-së." },
    { h: "Pëlqimet", p: "Pëlqimet për portal, email, SMS dhe AI regjistrohen me datë, mënyrë dhe IP, dhe mund të tërhiqen në çdo kohë." },
  ],
};

const privSr: LegalDoc = {
  title: "Politika privatnosti",
  updated: "Verzija 1.0 · Jul 2026 · Prema Zakonu br. 06/L-082",
  note: "Merodavan je tekst na albanskom jeziku.",
  sections: [
    { h: "Ko obrađuje podatke", p: "Kontrolor podataka je advokatska kancelarija koja vas zastupa. Operater AvokatIM je obrađivač i postupa isključivo po uputstvima kancelarije i DPA." },
    { h: "Šta se obrađuje", p: "Identifikacioni podaci (ime, lični broj, kontakt), podaci predmeta (podnesci, dokazi, prepiska), finansijski (fakture, sredstva u poverenju) i tehnički (logovi, IP, saglasnosti)." },
    { h: "Kako se čuvaju", p: "Dokumenti se čuvaju šifrovani. Indeksiranje se vrši lokalnim modelima — tekst se ne šalje van. Plaćanja karticom obrađuje pružalac plaćanja; podaci kartice se ne čuvaju." },
    { h: "Eksterna AI", p: "Ako je kancelarija aktivira, fragmenti pitanja i konteksta mogu se slati eksternom AI provajderu. To je jasno označeno u asistentu i može se potpuno isključiti." },
    { h: "Vaša prava", p: "Pristup, ispravka, brisanje (kada ne postoji zakonska obaveza čuvanja), ograničenje, prenosivost i povlačenje saglasnosti u svakom trenutku. Zahtevi se rešavaju u roku od 30 dana. Žalbe: Agencija za informisanje i privatnost (AIP)." },
    { h: "Čuvanje", p: "Dosijei se čuvaju koliko zahtevaju profesionalne, poreske i AML obaveze. Nakon isteka roka, predmeti se označavaju za pregled i odlučuje advokat." },
    { h: "Međunarodni prenosi", p: "Neki opcioni podobrađivači nalaze se van Kosova (eksterna AI, plaćanja, e-mail). Potpuna lista sa zaštitnim merama nalazi se u aneksu DPA." },
    { h: "Saglasnosti", p: "Saglasnosti za portal, e-mail, SMS i AI beleže se sa datumom, načinom i IP adresom i mogu se povući u svakom trenutku." },
  ],
};

const privTr: LegalDoc = {
  title: "Gizlilik Politikası",
  updated: "Sürüm 1.0 · Temmuz 2026 · 06/L-082 sayılı Kanun'a göre",
  note: "Bağlayıcı metin Arnavutça olandır.",
  sections: [
    { h: "Verileri kim işler", p: "Veri sorumlusu sizi temsil eden hukuk bürosudur. AvokatIM operatörü veri işleyendir ve yalnızca büronun talimatlarına ve DPA'ya göre hareket eder." },
    { h: "Neler işlenir", p: "Kimlik verileri (ad, kimlik no, iletişim), dosya verileri (dilekçeler, deliller, yazışmalar), mali veriler (faturalar, emanet fonlar) ve teknik veriler (loglar, IP, onaylar)." },
    { h: "Nasıl saklanır", p: "Belgeler şifreli saklanır. Dizinleme yerel modellerle yapılır — metin dışarı gönderilmez. Kart ödemeleri ödeme sağlayıcısı tarafından işlenir; kart verileri saklanmaz." },
    { h: "Harici AI", p: "Büro etkinleştirirse, soru ve bağlam parçaları harici AI sağlayıcısına gönderilebilir. Bu, asistanda açıkça belirtilir ve tamamen kapatılabilir." },
    { h: "Haklarınız", p: "Erişim, düzeltme, silme (yasal saklama yükümlülüğü yoksa), kısıtlama, taşınabilirlik ve onayı her an geri çekme. Talepler 30 gün içinde işlenir. Şikayet: Bilgi ve Mahremiyet Ajansı (AIP)." },
    { h: "Saklama", p: "Dosyalar mesleki, vergi ve AML yükümlülüklerinin gerektirdiği süre kadar saklanır. Süre dolunca dosyalar incelemeye işaretlenir ve avukat karar verir." },
    { h: "Uluslararası aktarımlar", p: "Bazı isteğe bağlı alt işleyiciler Kosova dışındadır (harici AI, ödemeler, e-posta). Koruyucu önlemleri içeren tam liste DPA ekindedir." },
    { h: "Onaylar", p: "Portal, e-posta, SMS ve AI onayları tarih, yöntem ve IP ile kaydedilir ve her an geri çekilebilir." },
  ],
};

const privBs: LegalDoc = {
  title: "Politika privatnosti",
  updated: "Verzija 1.0 · Juli 2026 · Prema Zakonu br. 06/L-082",
  note: "Mjerodavan je tekst na albanskom jeziku.",
  sections: [
    { h: "Ko obrađuje podatke", p: "Kontrolor podataka je advokatska kancelarija koja vas zastupa. Operater AvokatIM je obrađivač i postupa isključivo po uputama kancelarije i DPA." },
    { h: "Šta se obrađuje", p: "Identifikacioni podaci (ime, lični broj, kontakt), podaci predmeta (podnesci, dokazi, prepiska), finansijski (fakture, sredstva u povjerenju) i tehnički (logovi, IP, saglasnosti)." },
    { h: "Kako se čuvaju", p: "Dokumenti se čuvaju šifrirani. Indeksiranje se vrši lokalnim modelima — tekst se ne šalje van. Plaćanja karticom obrađuje pružalac plaćanja; podaci kartice se ne čuvaju." },
    { h: "Eksterna AI", p: "Ako je kancelarija aktivira, fragmenti pitanja i konteksta mogu se slati eksternom AI provajderu. To je jasno označeno u asistentu i može se potpuno isključiti." },
    { h: "Vaša prava", p: "Pristup, ispravka, brisanje (kada ne postoji zakonska obaveza čuvanja), ograničenje, prenosivost i povlačenje saglasnosti u svakom trenutku. Zahtjevi se rješavaju u roku od 30 dana. Žalbe: Agencija za informisanje i privatnost (AIP)." },
    { h: "Čuvanje", p: "Dosjei se čuvaju koliko zahtijevaju profesionalne, poreske i AML obaveze. Nakon isteka roka, predmeti se označavaju za pregled i odlučuje advokat." },
    { h: "Međunarodni prijenosi", p: "Neki opcionalni podobrađivači nalaze se van Kosova (eksterna AI, plaćanja, e-mail). Potpuna lista sa zaštitnim mjerama nalazi se u aneksu DPA." },
    { h: "Saglasnosti", p: "Saglasnosti za portal, e-mail, SMS i AI bilježe se s datumom, načinom i IP adresom i mogu se povući u svakom trenutku." },
  ],
};

const privEn: LegalDoc = {
  title: "Privacy Policy",
  updated: "Version 1.0 · July 2026 · Under Law No. 06/L-082",
  note: "The authoritative text is the Albanian version.",
  sections: [
    { h: "Who processes your data", p: "The data controller is the law firm representing you. The AvokatIM operator is a processor acting only on the firm's instructions and under the DPA." },
    { h: "What is processed", p: "Identification data (name, personal number, contact), case data (filings, evidence, correspondence), financial data (invoices, trust funds) and technical data (logs, IP, consents)." },
    { h: "How it is stored", p: "Documents are stored encrypted. Indexing uses local models — text never leaves the server. Card payments are handled by the payment provider; card data is not stored." },
    { h: "External AI", p: "If the firm enables it, fragments of questions and context may be sent to the external AI provider. This is clearly indicated in the assistant and can be fully disabled." },
    { h: "Your rights", p: "Access, rectification, erasure (where no legal retention duty exists), restriction, portability and withdrawal of consent at any time. Requests are handled within 30 days. Complaints: the Information and Privacy Agency (AIP)." },
    { h: "Retention", p: "Files are kept as long as professional, tax and AML obligations require. After expiry, matters are flagged for review and the lawyer decides." },
    { h: "International transfers", p: "Some optional sub-processors are located outside Kosovo (external AI, payments, email). The full list with safeguards is kept in the DPA annex." },
    { h: "Consents", p: "Consents for portal, email, SMS and AI are recorded with date, method and IP, and can be withdrawn at any time." },
  ],
};

const privZh: LegalDoc = {
  title: "隐私政策",
  updated: "版本 1.0 · 2026年7月 · 依据第06/L-082号法律",
  note: "以阿尔巴尼亚语文本为准。",
  sections: [
    { h: "谁处理您的数据", p: "数据控制者是代理您的律所。AvokatIM 运营方是数据处理者，仅根据律所的指示和数据处理协议行事。" },
    { h: "处理哪些数据", p: "身份数据（姓名、个人编号、联系方式）、案件数据（书状、证据、往来函件）、财务数据（发票、信托资金）和技术数据（日志、IP、同意记录）。" },
    { h: "如何存储", p: "文件加密存储。索引使用本地模型——文本不会离开服务器。银行卡支付由支付服务商处理；不存储卡片数据。" },
    { h: "外部 AI", p: "如果律所启用，问题和上下文片段可能会发送给外部 AI 提供商。这会在助手中明确标示，并可完全关闭。" },
    { h: "您的权利", p: "访问、更正、删除（无法定保存义务时）、限制、可携带以及随时撤回同意。请求在30天内处理。投诉：信息与隐私署（AIP）。" },
    { h: "保存期限", p: "档案按职业、税务和反洗钱义务要求的期限保存。到期后案件被标记供审查，由律师决定。" },
    { h: "国际传输", p: "某些可选的子处理者位于科索沃境外（外部 AI、支付、电子邮件）。带保障措施的完整清单载于数据处理协议附件。" },
    { h: "同意", p: "门户、电子邮件、短信和 AI 的同意均记录日期、方式和 IP，并可随时撤回。" },
  ],
};

export const TOS: Record<Locale, LegalDoc> = {
  sq: tosSq, sr: tosSr, tr: tosTr, bs: tosBs, en: tosEn, zh: tosZh,
};

export const PRIVACY: Record<Locale, LegalDoc> = {
  sq: privSq, sr: privSr, tr: privTr, bs: privBs, en: privEn, zh: privZh,
};
