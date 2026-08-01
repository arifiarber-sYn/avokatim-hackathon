// Curated public "Ratgeber" articles for the German market (D-045): the ten
// most-searched consumer law topics, written as general information (RDG-safe
// — no individual legal advice), each with a CTA toward Ava / posto-rastin.
// Static data, no CMS at this stage; content reviewed against the cited
// statutes as of 2026-08. German only — the articles target de.avokatiim.ai.

export interface RatgeberArticle {
  slug: string;
  /** Practice area chip shown on cards and the article header. */
  area: string;
  title: string;
  /** Meta description (~150 chars) and card teaser. */
  description: string;
  updated: string; // ISO date, for Article JSON-LD
  /** Key facts shown as a highlight box at the top. */
  facts: string[];
  sections: { h: string; p: string[] }[];
}

export const RATGEBER_ARTICLES: RatgeberArticle[] = [
  {
    slug: "kuendigung-arbeitsvertrag",
    area: "Arbeitsrecht",
    title: "Kündigung erhalten: Ihre Rechte und die 3-Wochen-Frist",
    description:
      "Nach einer Kündigung bleiben nur 3 Wochen für die Kündigungsschutzklage (§ 4 KSchG). Was Sie jetzt prüfen sollten — Fristen, Abfindung, Arbeitslosengeld.",
    updated: "2026-08-01",
    facts: [
      "Kündigungsschutzklage: nur 3 Wochen ab Zugang der Kündigung (§ 4 KSchG)",
      "Arbeitsuchend melden: innerhalb von 3 Tagen bei der Agentur für Arbeit",
      "Kündigung muss schriftlich mit Original-Unterschrift erfolgen (§ 623 BGB)",
    ],
    sections: [
      {
        h: "Die wichtigste Frist: 3 Wochen",
        p: [
          "Wer sich gegen eine Kündigung wehren will, muss innerhalb von drei Wochen nach Zugang des Kündigungsschreibens Kündigungsschutzklage beim Arbeitsgericht erheben (§ 4 KSchG). Versäumt man diese Frist, gilt die Kündigung grundsätzlich als wirksam — selbst wenn sie eigentlich angreifbar gewesen wäre.",
          "Der Zugang zählt, nicht das Datum auf dem Schreiben: Die Frist beginnt an dem Tag, an dem die Kündigung in Ihren Briefkasten gelangt oder Ihnen übergeben wird.",
        ],
      },
      {
        h: "Formfehler sind häufig",
        p: [
          "Eine Kündigung ist nur wirksam, wenn sie schriftlich erfolgt und im Original unterschrieben ist (§ 623 BGB). Kündigungen per E-Mail, WhatsApp oder Fax sind formunwirksam.",
          "In Betrieben mit mehr als zehn Vollzeit-Beschäftigten gilt zudem das Kündigungsschutzgesetz: Der Arbeitgeber braucht einen Kündigungsgrund (betriebs-, verhaltens- oder personenbedingt). Bei Schwangeren, Menschen mit Schwerbehinderung und Betriebsräten gelten Sonderkündigungsschutz-Regeln.",
        ],
      },
      {
        h: "Abfindung: kein Automatismus, aber oft verhandelbar",
        p: [
          "Ein gesetzlicher Anspruch auf Abfindung besteht nur in Ausnahmefällen (z. B. § 1a KSchG bei betriebsbedingter Kündigung mit entsprechendem Angebot). In der Praxis enden viele Kündigungsschutzverfahren dennoch mit einem Vergleich — als Faustformel gilt ein halbes Bruttomonatsgehalt pro Beschäftigungsjahr, verhandelbar nach Prozessrisiko.",
        ],
      },
      {
        h: "Was Sie sofort tun sollten",
        p: [
          "Melden Sie sich spätestens drei Tage nach Kenntnis der Kündigung arbeitsuchend, um Sperrzeiten beim Arbeitslosengeld zu vermeiden. Sammeln Sie Arbeitsvertrag, Kündigungsschreiben, Lohnabrechnungen und Zeugnisse. Und lassen Sie die Erfolgsaussichten einer Klage schnell prüfen — wegen der 3-Wochen-Frist zählt jeder Tag.",
        ],
      },
    ],
  },
  {
    slug: "mietminderung",
    area: "Mietrecht",
    title: "Mietminderung bei Mängeln: Wann und wie viel?",
    description:
      "Schimmel, Heizungsausfall, Baulärm: Bei erheblichen Mängeln dürfen Mieter die Miete mindern (§ 536 BGB). So gehen Sie richtig vor, ohne die Kündigung zu riskieren.",
    updated: "2026-08-01",
    facts: [
      "Minderung kraft Gesetzes bei erheblichen Mängeln (§ 536 BGB)",
      "Erst den Mangel anzeigen — ohne Mängelanzeige keine Minderung",
      "Zu hohe Minderung kann zur Kündigung wegen Zahlungsverzugs führen",
    ],
    sections: [
      {
        h: "Das Recht auf Mietminderung",
        p: [
          "Weist die Wohnung einen Mangel auf, der ihre Tauglichkeit zum vertragsgemäßen Gebrauch erheblich mindert, ist die Miete kraft Gesetzes herabgesetzt (§ 536 BGB) — eine Zustimmung des Vermieters ist nicht erforderlich. Typische Fälle: Schimmelbefall, Heizungsausfall im Winter, Wasserschaden, dauerhafter Baulärm, Ausfall von Warmwasser oder Aufzug.",
        ],
      },
      {
        h: "Erster Schritt: Mängelanzeige",
        p: [
          "Zeigen Sie den Mangel dem Vermieter unverzüglich und nachweisbar an (§ 536c BGB), am besten schriftlich mit Fristsetzung zur Beseitigung. Wer den Mangel nicht anzeigt, verliert für diesen Zeitraum das Minderungsrecht und kann sich sogar schadensersatzpflichtig machen.",
          "Dokumentieren Sie den Mangel mit Fotos, Datum und Zeugen — das ist später die Grundlage für die Minderungsquote.",
        ],
      },
      {
        h: "Wie hoch darf die Minderung sein?",
        p: [
          "Die Quote richtet sich nach der Schwere der Beeinträchtigung im Einzelfall; Gerichte haben z. B. bei komplettem Heizungsausfall im Winter Minderungen von 70–100 %, bei Schimmel je nach Ausmaß 10–25 % anerkannt. Gemindert wird von der Bruttomiete (inkl. Nebenkosten).",
          "Vorsicht: Wer zu hoch mindert, gerät in Zahlungsverzug — ab zwei Monatsmieten Rückstand droht die fristlose Kündigung. Sicherer Weg: unter Vorbehalt weiterzahlen und die Minderung rückwirkend geltend machen.",
        ],
      },
    ],
  },
  {
    slug: "fluggastrechte",
    area: "Reiserecht",
    title: "Flug verspätet oder annulliert: bis zu 600 € Entschädigung",
    description:
      "Ab 3 Stunden Verspätung am Ziel haben Fluggäste nach EU-Verordnung 261/2004 Anspruch auf 250–600 € Ausgleichszahlung. Voraussetzungen, Ausnahmen, Verjährung.",
    updated: "2026-08-01",
    facts: [
      "250 € / 400 € / 600 € je nach Flugstrecke (EU-VO 261/2004)",
      "Ab 3 Stunden Verspätung an der Endstation",
      "Verjährung: 3 Jahre zum Jahresende (§§ 195, 199 BGB)",
    ],
    sections: [
      {
        h: "Wann besteht der Anspruch?",
        p: [
          "Die EU-Fluggastrechteverordnung 261/2004 gewährt eine pauschale Ausgleichszahlung bei Annullierung, Nichtbeförderung (Überbuchung) und — nach der Rechtsprechung des EuGH — bei Ankunftsverspätung ab drei Stunden: 250 € bis 1.500 km, 400 € bis 3.500 km, 600 € darüber.",
          "Die Verordnung gilt für alle Abflüge aus der EU sowie für Flüge in die EU mit einer EU-Airline.",
        ],
      },
      {
        h: "Ausnahme: außergewöhnliche Umstände",
        p: [
          "Keine Entschädigung gibt es bei außergewöhnlichen Umständen, die sich auch mit allen zumutbaren Maßnahmen nicht vermeiden ließen — etwa Unwetter, Fluglotsenstreik oder Vogelschlag. Technische Defekte und Streiks des eigenen Personals der Airline zählen nach der Rechtsprechung regelmäßig nicht dazu.",
        ],
      },
      {
        h: "Zusätzliche Rechte am Flughafen",
        p: [
          "Unabhängig von der Ausgleichszahlung schuldet die Airline Betreuungsleistungen: Verpflegung, zwei Telefonate/E-Mails und bei Übernachtung ein Hotel samt Transfer. Bei mehr als fünf Stunden Verspätung können Sie vom Flug zurücktreten und den Ticketpreis zurückverlangen.",
          "Der Anspruch verjährt in drei Jahren zum Jahresende. Übrigens: Für Klagen bis 10.000 € gegen Airlines gibt es seit April 2026 an mehreren Amtsgerichten das zivilgerichtliche Online-Verfahren.",
        ],
      },
    ],
  },
  {
    slug: "abmahnung-arbeitsrecht",
    area: "Arbeitsrecht",
    title: "Abmahnung im Job: Was jetzt zu tun ist",
    description:
      "Eine Abmahnung ist die Vorstufe zur verhaltensbedingten Kündigung. Wann sie berechtigt ist, wie Sie reagieren und wann eine Gegendarstellung sinnvoll ist.",
    updated: "2026-08-01",
    facts: [
      "Abmahnung = Rüge + Warnfunktion vor der Kündigung",
      "Keine gesetzliche Frist: auch Wochen später noch angreifbar",
      "Recht auf Gegendarstellung zur Personalakte (§ 83 Abs. 2 BetrVG)",
    ],
    sections: [
      {
        h: "Funktion der Abmahnung",
        p: [
          "Mit der Abmahnung rügt der Arbeitgeber einen konkreten Pflichtverstoß und warnt zugleich: Im Wiederholungsfall droht die Kündigung. Ohne vorherige einschlägige Abmahnung ist eine verhaltensbedingte Kündigung in aller Regel unwirksam.",
          "Eine wirksame Abmahnung muss das beanstandete Verhalten konkret benennen (Datum, Situation) — pauschale Vorwürfe wie „mangelnde Motivation“ genügen nicht.",
        ],
      },
      {
        h: "Nicht vorschnell unterschreiben",
        p: [
          "Sie sind nicht verpflichtet, die Abmahnung zu unterschreiben oder den Vorwurf anzuerkennen. Bestätigen Sie höchstens den Empfang. Prüfen Sie in Ruhe: Stimmt der Sachverhalt? Ist der Vorwurf konkret genug? War das Verhalten überhaupt pflichtwidrig?",
        ],
      },
      {
        h: "Ihre Reaktionsmöglichkeiten",
        p: [
          "Sie können eine Gegendarstellung zur Personalakte einreichen, die Entfernung einer unberechtigten Abmahnung verlangen und notfalls einklagen. Taktisch ist es oft klüger, die Gegendarstellung zu dokumentieren und die Abmahnung erst im späteren Kündigungsschutzprozess anzugreifen — dort muss der Arbeitgeber die Berechtigung beweisen.",
        ],
      },
    ],
  },
  {
    slug: "mahnbescheid",
    area: "Zivilrecht",
    title: "Mahnbescheid erhalten: 14 Tage für den Widerspruch",
    description:
      "Ein gerichtlicher Mahnbescheid ist keine Rechnung — ohne Widerspruch binnen 2 Wochen droht der Vollstreckungsbescheid. So reagieren Sie richtig (§§ 692 ff. ZPO).",
    updated: "2026-08-01",
    facts: [
      "Widerspruchsfrist: 2 Wochen ab Zustellung (§ 692 ZPO)",
      "Das Mahngericht prüft die Forderung inhaltlich nicht",
      "Nach Vollstreckungsbescheid: nur noch 2 Wochen Einspruch (§ 700 ZPO)",
    ],
    sections: [
      {
        h: "Was der Mahnbescheid bedeutet",
        p: [
          "Der Mahnbescheid ergeht im automatisierten gerichtlichen Mahnverfahren (§§ 688 ff. ZPO). Wichtig zu wissen: Das Gericht prüft nicht, ob die Forderung berechtigt ist. Auch völlig unbegründete oder überhöhte Forderungen können per Mahnbescheid geltend gemacht werden.",
        ],
      },
      {
        h: "Die 2-Wochen-Frist",
        p: [
          "Halten Sie die Forderung ganz oder teilweise für unberechtigt, legen Sie innerhalb von zwei Wochen ab Zustellung Widerspruch ein — das beigefügte Formular genügt, eine Begründung ist nicht nötig. Der Widerspruch verhindert den Vollstreckungsbescheid; die Sache geht dann ins normale streitige Verfahren über.",
          "Reagieren Sie nicht, kann der Gläubiger einen Vollstreckungsbescheid beantragen — aus diesem kann sofort vollstreckt werden (Kontopfändung, Gerichtsvollzieher). Dagegen hilft nur noch der Einspruch binnen zwei Wochen (§ 700 ZPO).",
        ],
      },
      {
        h: "Berechtigte Forderung?",
        p: [
          "Ist die Forderung berechtigt, sollten Sie zahlen — jeder weitere Verfahrensschritt erhöht die Kosten, die Sie am Ende tragen. Bei Zahlungsschwierigkeiten lohnt es sich, mit dem Gläubiger eine Ratenzahlung zu vereinbaren, bevor vollstreckt wird.",
        ],
      },
    ],
  },
  {
    slug: "mietkaution",
    area: "Mietrecht",
    title: "Mietkaution zurückfordern: Fristen und Abzüge",
    description:
      "Nach dem Auszug muss der Vermieter die Kaution samt Zinsen abrechnen. Welche Abzüge erlaubt sind, wie lange er prüfen darf und wie Sie die Rückzahlung durchsetzen.",
    updated: "2026-08-01",
    facts: [
      "Maximal 3 Nettokaltmieten Kaution (§ 551 BGB)",
      "Übliche Prüf- und Abrechnungsfrist: 3–6 Monate nach Rückgabe",
      "Anspruch verjährt in 3 Jahren zum Jahresende",
    ],
    sections: [
      {
        h: "Ihre Rechte an der Kaution",
        p: [
          "Die Kaution darf höchstens drei Nettokaltmieten betragen und muss vom Vermieter getrennt vom eigenen Vermögen verzinslich angelegt werden (§ 551 BGB). Die Zinsen stehen dem Mieter zu.",
        ],
      },
      {
        h: "Wann muss zurückgezahlt werden?",
        p: [
          "Eine starre gesetzliche Frist gibt es nicht: Der Vermieter hat eine angemessene Prüffrist, die die Rechtsprechung je nach Fall mit etwa drei bis sechs Monaten nach Wohnungsrückgabe bemisst. Für noch offene Betriebskostenabrechnungen darf er einen angemessenen Teil einbehalten — nicht aber die gesamte Kaution.",
        ],
      },
      {
        h: "Zulässige und unzulässige Abzüge",
        p: [
          "Abziehen darf der Vermieter offene Mieten, berechtigte Schadensersatzforderungen und Nachzahlungen aus Nebenkostenabrechnungen. Nicht abziehen darf er Kosten für normale Abnutzung (Gebrauchsspuren, ausgeblichene Tapeten) — und Schönheitsreparatur-Klauseln sind nach der BGH-Rechtsprechung häufig unwirksam, etwa bei unrenoviert übergebenen Wohnungen.",
          "Zahlt der Vermieter nicht, fordern Sie ihn schriftlich mit Frist auf. Danach können Sie den Anspruch gerichtlich geltend machen — bei Beträgen bis 10.000 € ggf. im neuen Online-Verfahren der Pilot-Amtsgerichte.",
        ],
      },
    ],
  },
  {
    slug: "nebenkostenabrechnung",
    area: "Mietrecht",
    title: "Nebenkostenabrechnung prüfen: die häufigsten Fehler",
    description:
      "Rund jede zweite Nebenkostenabrechnung ist fehlerhaft. Die 12-Monats-Frist des Vermieters, Ihre Einwendungsfrist und welche Posten gar nicht umlagefähig sind.",
    updated: "2026-08-01",
    facts: [
      "Abrechnungsfrist des Vermieters: 12 Monate nach Ende des Abrechnungszeitraums (§ 556 BGB)",
      "Einwendungsfrist des Mieters: 12 Monate nach Zugang der Abrechnung",
      "Umlagefähig sind nur Betriebskosten nach der BetrKV",
    ],
    sections: [
      {
        h: "Fristen auf beiden Seiten",
        p: [
          "Der Vermieter muss die Abrechnung spätestens zwölf Monate nach Ende des Abrechnungszeitraums zustellen (§ 556 Abs. 3 BGB); danach kann er Nachforderungen grundsätzlich nicht mehr verlangen. Umgekehrt müssen Sie Einwendungen innerhalb von zwölf Monaten nach Zugang der Abrechnung erheben — später sind sie ausgeschlossen.",
        ],
      },
      {
        h: "Was überhaupt umgelegt werden darf",
        p: [
          "Umlagefähig sind nur die in der Betriebskostenverordnung (BetrKV) genannten laufenden Kosten: z. B. Grundsteuer, Wasser, Heizung, Hausreinigung, Gartenpflege, Versicherungen, Hauswart. Nicht umlagefähig sind Instandhaltung und Reparaturen, Verwaltungskosten und Bankgebühren — diese Posten tauchen dennoch erstaunlich oft auf.",
        ],
      },
      {
        h: "So prüfen Sie konkret",
        p: [
          "Vergleichen Sie den Verteilerschlüssel mit dem Mietvertrag, prüfen Sie die Gesamtkosten auf ungewöhnliche Sprünge zum Vorjahr und verlangen Sie Belegeinsicht — darauf haben Sie ein Recht. Bis zur Klärung strittiger Positionen dürfen Sie die Nachzahlung insoweit zurückhalten.",
        ],
      },
    ],
  },
  {
    slug: "aufhebungsvertrag",
    area: "Arbeitsrecht",
    title: "Aufhebungsvertrag: Vorsicht vor der Sperrzeit",
    description:
      "Ein Aufhebungsvertrag klingt nach sauberem Abschied — kann aber 12 Wochen Sperrzeit beim Arbeitslosengeld kosten (§ 159 SGB III). Was vor der Unterschrift zu prüfen ist.",
    updated: "2026-08-01",
    facts: [
      "Kein Widerruf: einmal unterschrieben, bindet der Vertrag",
      "Sperrzeit-Risiko: bis zu 12 Wochen ALG I (§ 159 SGB III)",
      "Schriftform zwingend (§ 623 BGB) — keine E-Mail, kein Scan",
    ],
    sections: [
      {
        h: "Warum Arbeitgeber ihn anbieten",
        p: [
          "Mit dem Aufhebungsvertrag endet das Arbeitsverhältnis einvernehmlich — ohne Kündigungsfristen, ohne Kündigungsschutzverfahren, ohne Betriebsratsanhörung. Das ist vor allem für den Arbeitgeber attraktiv. Für Sie kann er sinnvoll sein, wenn die Konditionen stimmen: Abfindung, Freistellung, gutes Zeugnis, Beendigungszeitpunkt.",
        ],
      },
      {
        h: "Das Sperrzeit-Risiko",
        p: [
          "Wer sein Arbeitsverhältnis selbst löst, ohne wichtigen Grund, riskiert zwölf Wochen Sperrzeit beim Arbeitslosengeld (§ 159 SGB III) — und der Anspruchszeitraum verkürzt sich insgesamt. Die Sperrzeit lässt sich u. a. vermeiden, wenn eine betriebsbedingte Kündigung mit Auslauffrist konkret drohte und die Abfindung sich im Rahmen von 0,25 bis 0,5 Monatsgehältern pro Jahr bewegt — die Details sind kompliziert und sollten vor der Unterschrift geklärt sein.",
        ],
      },
      {
        h: "Vor der Unterschrift",
        p: [
          "Lassen Sie sich nicht unter Zeitdruck setzen — „nur heute gültig“ ist ein Warnsignal. Ein unterschriebener Aufhebungsvertrag kann grundsätzlich nicht widerrufen werden. Prüfen Sie Abfindungshöhe, Zeugnisnote, Resturlaub, Boni und Wettbewerbsverbote, und klären Sie die sozialversicherungsrechtlichen Folgen vor der Unterschrift.",
        ],
      },
    ],
  },
  {
    slug: "widerruf-online-kauf",
    area: "Verbraucherrecht",
    title: "Widerrufsrecht beim Online-Kauf: 14 Tage — und die Ausnahmen",
    description:
      "Online-Käufe können Verbraucher 14 Tage ohne Begründung widerrufen (§§ 312g, 355 BGB). Welche Ausnahmen gelten, wer die Rücksendekosten trägt und was bei fehlender Belehrung gilt.",
    updated: "2026-08-01",
    facts: [
      "14 Tage Widerrufsfrist ab Erhalt der Ware (§ 355 BGB)",
      "Ohne ordnungsgemäße Belehrung: Frist verlängert sich auf 12 Monate + 14 Tage",
      "Rückzahlung binnen 14 Tagen nach Widerruf",
    ],
    sections: [
      {
        h: "So funktioniert der Widerruf",
        p: [
          "Bei Fernabsatzverträgen — Online-Shop, Telefon, Katalog — können Verbraucher den Vertrag innerhalb von 14 Tagen ab Erhalt der Ware ohne Angabe von Gründen widerrufen (§§ 312g, 355 BGB). Der Widerruf muss eindeutig erklärt werden (E-Mail genügt); das bloße Zurücksenden der Ware reicht formal nicht aus, wird aber von vielen Shops akzeptiert.",
          "Hat der Händler nicht ordnungsgemäß über das Widerrufsrecht belehrt, verlängert sich die Frist auf zwölf Monate und 14 Tage.",
        ],
      },
      {
        h: "Wichtige Ausnahmen",
        p: [
          "Kein Widerrufsrecht besteht u. a. bei nach Kundenwunsch angefertigten Waren, schnell verderblichen Lebensmitteln, entsiegelten Hygieneartikeln, entsiegelten Datenträgern sowie bei Verträgen zwischen Unternehmern. Auch im stationären Ladengeschäft gibt es — anders als viele denken — kein gesetzliches Umtauschrecht.",
        ],
      },
      {
        h: "Geld zurück",
        p: [
          "Nach dem Widerruf muss der Händler den Kaufpreis inklusive Standard-Versandkosten binnen 14 Tagen erstatten; er darf warten, bis die Ware zurück ist oder der Rückversand nachgewiesen wird. Die Rücksendekosten trägt der Verbraucher nur, wenn der Händler darüber ordnungsgemäß belehrt hat. Ein Wertersatz ist nur bei übermäßiger Nutzung fällig — das Ausprobieren wie im Laden bleibt kostenfrei.",
        ],
      },
    ],
  },
  {
    slug: "verkehrsunfall",
    area: "Verkehrsrecht",
    title: "Verkehrsunfall: Schadensersatz richtig geltend machen",
    description:
      "Nach einem unverschuldeten Unfall zahlt die gegnerische Haftpflicht — auch Ihren Anwalt. Welche Positionen ersetzt werden und welche Fehler die Ansprüche mindern.",
    updated: "2026-08-01",
    facts: [
      "Freie Werkstatt- und Gutachterwahl beim Haftpflichtschaden",
      "Anwaltskosten trägt beim unverschuldeten Unfall die gegnerische Versicherung",
      "Ansprüche: Reparatur, Wertminderung, Nutzungsausfall, Schmerzensgeld",
    ],
    sections: [
      {
        h: "Am Unfallort",
        p: [
          "Sichern Sie die Unfallstelle, dokumentieren Sie alles mit Fotos (Fahrzeuge, Positionen, Kennzeichen, Spuren) und notieren Sie Zeugen. Geben Sie kein Schuldanerkenntnis ab — auch nicht „zur Vereinfachung“. Bei Personenschäden oder unklarer Sachlage rufen Sie die Polizei.",
        ],
      },
      {
        h: "Ihre Ansprüche gegen die gegnerische Versicherung",
        p: [
          "Beim unverschuldeten Unfall ersetzt die gegnerische Kfz-Haftpflicht (§ 7 StVG, § 823 BGB) mehr als nur die Reparatur: merkantile Wertminderung, Nutzungsausfall oder Mietwagen, Abschleppkosten, Gutachterkosten, eine Unkostenpauschale und bei Verletzungen Schmerzensgeld und Verdienstausfall.",
          "Ab einem Schaden oberhalb der Bagatellgrenze (ca. 750–1.000 €) dürfen Sie einen eigenen Sachverständigen beauftragen — auf Kosten der Versicherung. Sie müssen sich nicht auf den Gutachter der Gegenseite verlassen.",
        ],
      },
      {
        h: "Vorsicht bei schnellen Angeboten",
        p: [
          "Versicherer regulieren gern schnell und niedrig: pauschale Abfindungsangebote, Verweis auf günstigere Referenzwerkstätten, Kürzung des Nutzungsausfalls. Wichtig zu wissen: Die Kosten eines eigenen Anwalts gehören beim unverschuldeten Unfall zum ersatzfähigen Schaden — die Durchsetzung kostet Sie in diesem Fall nichts extra.",
        ],
      },
    ],
  },
  {
    slug: "prozesskosten",
    area: "Zivilrecht",
    title: "Was kostet ein Gerichtsverfahren? Prozesskosten verständlich erklärt",
    description:
      "Gerichtskosten, Anwaltsgebühren, Kostenrisiko: Wer verliert, zahlt alles (§ 91 ZPO). Wie sich Prozesskosten berechnen und welche Hilfen es gibt — PKH, Beratungshilfe, Rechtsschutz.",
    updated: "2026-08-01",
    facts: [
      "Der Verlierer trägt sämtliche Kosten beider Seiten (§ 91 ZPO)",
      "Gebühren richten sich nach dem Streitwert (RVG, GKG)",
      "Hilfen: Prozesskostenhilfe, Beratungshilfe, Rechtsschutzversicherung",
    ],
    sections: [
      {
        h: "Das Kostenprinzip",
        p: [
          "Im deutschen Zivilprozess gilt: Die unterlegene Partei trägt die Kosten des Rechtsstreits — die Gerichtskosten und die gesetzlichen Anwaltsgebühren beider Seiten (§ 91 ZPO). Bei teilweisem Obsiegen werden die Kosten entsprechend gequotelt.",
          "Alle Gebühren richten sich nach dem Streitwert: Die Anwaltsgebühren folgen dem Rechtsanwaltsvergütungsgesetz (RVG), die Gerichtskosten dem Gerichtskostengesetz (GKG). Bei Klageeinreichung ist ein Gerichtskostenvorschuss von in der Regel drei Gebühren zu zahlen.",
        ],
      },
      {
        h: "Ein Gefühl für die Größenordnung",
        p: [
          "Bei einem Streitwert von 5.000 € liegt das Gesamtrisiko der ersten Instanz — eigener Anwalt, gegnerischer Anwalt, Gericht — grob bei 3.000 €; mit Berufung steigt es deutlich. Für eine genaue Berechnung über alle Instanzen gibt es unseren kostenlosen Prozesskostenrechner.",
        ],
      },
      {
        h: "Wenn das Geld nicht reicht",
        p: [
          "Wer die Kosten nicht aufbringen kann, hat Anspruch auf Prozesskostenhilfe (PKH), wenn die Klage hinreichende Erfolgsaussicht hat — sie deckt Gerichtskosten und den eigenen Anwalt (Achtung: bei Niederlage bleibt der gegnerische Anwalt zu zahlen). Für die außergerichtliche Beratung gibt es Beratungshilfe. Und eine bestehende Rechtsschutzversicherung übernimmt je nach Police Deckung für viele Streitigkeiten — die Deckungsanfrage stellt der Anwalt in der Regel kostenfrei für Sie.",
        ],
      },
    ],
  },
];

export function ratgeberBySlug(slug: string): RatgeberArticle | undefined {
  return RATGEBER_ARTICLES.find((a) => a.slug === slug);
}
