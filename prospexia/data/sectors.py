"""Catalogue des secteurs d'activité, prétraduits dans les langues principales.

Les langues absentes du catalogue sont traduites à la volée (voir core/translate.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Sector:
    key: str
    label_fr: str
    category: str
    translations: dict[str, str] = field(default_factory=dict)  # lang -> terme de recherche

    def term(self, lang: str) -> str | None:
        if lang == "fr":
            return self.label_fr
        return self.translations.get(lang)


def _s(key: str, fr: str, cat: str, en: str, de: str, es: str, it: str, pt: str, nl: str) -> Sector:
    return Sector(key, fr, cat, {"en": en, "de": de, "es": es, "it": it, "pt": pt, "nl": nl})


SECTORS: list[Sector] = [
    # --- Bâtiment & artisanat ---
    _s("plombier", "Plombier", "Bâtiment & artisanat", "plumber", "Klempner", "fontanero", "idraulico", "canalizador", "loodgieter"),
    _s("electricien", "Électricien", "Bâtiment & artisanat", "electrician", "Elektriker", "electricista", "elettricista", "eletricista", "elektricien"),
    _s("menuisier", "Menuisier", "Bâtiment & artisanat", "carpenter", "Schreiner", "carpintero", "falegname", "carpinteiro", "timmerman"),
    _s("macon", "Maçon", "Bâtiment & artisanat", "masonry contractor", "Maurer", "albañil", "muratore", "pedreiro", "metselaar"),
    _s("peintre_batiment", "Peintre en bâtiment", "Bâtiment & artisanat", "house painter", "Maler", "pintor de casas", "imbianchino", "pintor de casas", "schilder"),
    _s("couvreur", "Couvreur", "Bâtiment & artisanat", "roofer", "Dachdecker", "techador", "copritetto", "telhador", "dakdekker"),
    _s("chauffagiste", "Chauffagiste", "Bâtiment & artisanat", "heating contractor", "Heizungsbauer", "instalador de calefacción", "termoidraulico", "instalador de aquecimento", "verwarmingsinstallateur"),
    _s("serrurier", "Serrurier", "Bâtiment & artisanat", "locksmith", "Schlüsseldienst", "cerrajero", "fabbro", "chaveiro", "slotenmaker"),
    _s("carreleur", "Carreleur", "Bâtiment & artisanat", "tiler", "Fliesenleger", "alicatador", "piastrellista", "ladrilhador", "tegelzetter"),
    _s("paysagiste", "Paysagiste / jardinier", "Bâtiment & artisanat", "landscaper", "Gartenbau", "jardinero", "giardiniere", "jardineiro", "hovenier"),
    _s("entreprise_renovation", "Entreprise de rénovation", "Bâtiment & artisanat", "renovation contractor", "Renovierungsfirma", "empresa de reformas", "impresa di ristrutturazioni", "empresa de remodelação", "renovatiebedrijf"),
    _s("architecte", "Architecte", "Bâtiment & artisanat", "architect", "Architekt", "arquitecto", "architetto", "arquiteto", "architect"),
    # --- Restauration & alimentation ---
    _s("restaurant", "Restaurant", "Restauration & alimentation", "restaurant", "Restaurant", "restaurante", "ristorante", "restaurante", "restaurant"),
    _s("boulangerie", "Boulangerie-pâtisserie", "Restauration & alimentation", "bakery", "Bäckerei", "panadería", "panetteria", "padaria", "bakkerij"),
    _s("boucherie", "Boucherie-charcuterie", "Restauration & alimentation", "butcher shop", "Metzgerei", "carnicería", "macelleria", "talho", "slagerij"),
    _s("traiteur", "Traiteur", "Restauration & alimentation", "caterer", "Partyservice", "catering", "catering", "catering", "cateraar"),
    _s("bar_cafe", "Bar / café", "Restauration & alimentation", "bar cafe", "Café Bar", "bar cafetería", "bar caffè", "bar café", "café bar"),
    _s("pizzeria", "Pizzeria", "Restauration & alimentation", "pizzeria", "Pizzeria", "pizzería", "pizzeria", "pizzaria", "pizzeria"),
    _s("epicerie", "Épicerie fine / primeur", "Restauration & alimentation", "grocery store", "Feinkostladen", "tienda de alimentación", "alimentari", "mercearia", "kruidenier"),
    _s("fromagerie_cave", "Fromagerie / cave à vin", "Restauration & alimentation", "wine shop", "Weinhandlung", "vinoteca", "enoteca", "garrafeira", "wijnhandel"),
    # --- Beauté & bien-être ---
    _s("coiffeur", "Salon de coiffure", "Beauté & bien-être", "hair salon", "Friseur", "peluquería", "parrucchiere", "cabeleireiro", "kapper"),
    _s("institut_beaute", "Institut de beauté", "Beauté & bien-être", "beauty salon", "Kosmetikstudio", "salón de belleza", "centro estetico", "salão de beleza", "schoonheidssalon"),
    _s("barbier", "Barbier", "Beauté & bien-être", "barber shop", "Barbier", "barbería", "barbiere", "barbearia", "barbier"),
    _s("onglerie", "Onglerie", "Beauté & bien-être", "nail salon", "Nagelstudio", "salón de uñas", "nail salon", "salão de manicure", "nagelstudio"),
    _s("spa_massage", "Spa / massage", "Beauté & bien-être", "massage spa", "Massagepraxis", "centro de masajes", "centro massaggi", "centro de massagens", "massagesalon"),
    _s("tatoueur", "Salon de tatouage", "Beauté & bien-être", "tattoo studio", "Tattoostudio", "estudio de tatuajes", "studio tatuaggi", "estúdio de tatuagem", "tattooshop"),
    _s("salle_sport", "Salle de sport / coach", "Beauté & bien-être", "gym fitness", "Fitnessstudio", "gimnasio", "palestra", "ginásio", "sportschool"),
    _s("yoga_pilates", "Studio yoga / pilates", "Beauté & bien-être", "yoga studio", "Yogastudio", "estudio de yoga", "studio yoga", "estúdio de yoga", "yogastudio"),
    # --- Santé ---
    _s("dentiste", "Dentiste", "Santé", "dentist", "Zahnarzt", "dentista", "dentista", "dentista", "tandarts"),
    _s("kinesitherapeute", "Kinésithérapeute", "Santé", "physiotherapist", "Physiotherapeut", "fisioterapeuta", "fisioterapista", "fisioterapeuta", "fysiotherapeut"),
    _s("osteopathe", "Ostéopathe", "Santé", "osteopath", "Osteopath", "osteópata", "osteopata", "osteopata", "osteopaat"),
    _s("veterinaire", "Vétérinaire", "Santé", "veterinarian", "Tierarzt", "veterinario", "veterinario", "veterinário", "dierenarts"),
    _s("opticien", "Opticien", "Santé", "optician", "Optiker", "óptica", "ottico", "ótica", "opticien"),
    _s("pharmacie", "Pharmacie", "Santé", "pharmacy", "Apotheke", "farmacia", "farmacia", "farmácia", "apotheek"),
    _s("psychologue", "Psychologue", "Santé", "psychologist", "Psychologe", "psicólogo", "psicologo", "psicólogo", "psycholoog"),
    # --- Automobile ---
    _s("garage_auto", "Garage automobile", "Automobile", "auto repair shop", "Autowerkstatt", "taller mecánico", "officina meccanica", "oficina mecânica", "autogarage"),
    _s("carrosserie", "Carrosserie", "Automobile", "auto body shop", "Karosseriewerkstatt", "taller de chapa y pintura", "carrozzeria", "oficina de chapa e pintura", "carrosseriebedrijf"),
    _s("lavage_auto", "Lavage auto", "Automobile", "car wash", "Autowaschanlage", "lavado de coches", "autolavaggio", "lavagem de carros", "autowasstraat"),
    _s("concessionnaire", "Concessionnaire / vente auto", "Automobile", "used car dealer", "Autohändler", "concesionario de coches", "concessionaria auto", "stand de automóveis", "autodealer"),
    _s("auto_ecole", "Auto-école", "Automobile", "driving school", "Fahrschule", "autoescuela", "autoscuola", "escola de condução", "rijschool"),
    _s("pneus", "Centre pneus / vidange", "Automobile", "tire shop", "Reifenservice", "taller de neumáticos", "gommista", "loja de pneus", "bandenservice"),
    # --- Commerce ---
    _s("fleuriste", "Fleuriste", "Commerce", "florist", "Blumenladen", "floristería", "fioraio", "florista", "bloemist"),
    _s("boutique_vetements", "Boutique de vêtements", "Commerce", "clothing store", "Bekleidungsgeschäft", "tienda de ropa", "negozio di abbigliamento", "loja de roupa", "kledingwinkel"),
    _s("bijouterie", "Bijouterie", "Commerce", "jewelry store", "Juwelier", "joyería", "gioielleria", "joalharia", "juwelier"),
    _s("librairie", "Librairie / papeterie", "Commerce", "bookstore", "Buchhandlung", "librería", "libreria", "livraria", "boekhandel"),
    _s("magasin_meubles", "Magasin de meubles / décoration", "Commerce", "furniture store", "Möbelgeschäft", "tienda de muebles", "negozio di mobili", "loja de móveis", "meubelwinkel"),
    _s("animalerie", "Animalerie / toilettage", "Commerce", "pet store", "Zoohandlung", "tienda de mascotas", "negozio di animali", "loja de animais", "dierenwinkel"),
    _s("quincaillerie", "Quincaillerie / bricolage", "Commerce", "hardware store", "Eisenwarenhandlung", "ferretería", "ferramenta", "loja de ferragens", "ijzerwarenwinkel"),
    _s("pressing", "Pressing / laverie", "Commerce", "dry cleaner", "Reinigung", "tintorería", "lavanderia", "lavandaria", "stomerij"),
    _s("reparation_tel", "Réparation téléphone / informatique", "Commerce", "phone repair shop", "Handy Reparatur", "reparación de móviles", "riparazione cellulari", "reparação de telemóveis", "telefoon reparatie"),
    # --- Services & professions libérales ---
    _s("avocat", "Avocat", "Services", "lawyer", "Rechtsanwalt", "abogado", "avvocato", "advogado", "advocaat"),
    _s("expert_comptable", "Expert-comptable", "Services", "accountant", "Steuerberater", "asesoría contable", "commercialista", "contabilista", "accountant"),
    _s("agence_immobiliere", "Agence immobilière", "Services", "real estate agency", "Immobilienmakler", "inmobiliaria", "agenzia immobiliare", "imobiliária", "makelaar"),
    _s("assurance", "Courtier en assurance", "Services", "insurance broker", "Versicherungsmakler", "correduría de seguros", "broker assicurativo", "corretor de seguros", "verzekeringsmakelaar"),
    _s("notaire", "Notaire", "Services", "notary", "Notar", "notaría", "notaio", "notário", "notaris"),
    _s("demenagement", "Déménagement", "Services", "moving company", "Umzugsunternehmen", "empresa de mudanzas", "traslochi", "empresa de mudanças", "verhuisbedrijf"),
    _s("nettoyage", "Entreprise de nettoyage", "Services", "cleaning company", "Reinigungsfirma", "empresa de limpieza", "impresa di pulizie", "empresa de limpeza", "schoonmaakbedrijf"),
    _s("securite", "Sécurité / gardiennage", "Services", "security company", "Sicherheitsdienst", "empresa de seguridad", "vigilanza privata", "empresa de segurança", "beveiligingsbedrijf"),
    _s("photographe", "Photographe", "Services", "photographer", "Fotograf", "fotógrafo", "fotografo", "fotógrafo", "fotograaf"),
    _s("imprimerie", "Imprimerie", "Services", "print shop", "Druckerei", "imprenta", "tipografia", "gráfica", "drukkerij"),
    _s("taxi_vtc", "Taxi / VTC", "Services", "taxi service", "Taxiunternehmen", "taxi", "taxi", "táxi", "taxibedrijf"),
    _s("garde_enfants", "Crèche / garde d'enfants", "Services", "daycare", "Kindertagesstätte", "guardería", "asilo nido", "creche", "kinderdagverblijf"),
    _s("soutien_scolaire", "Soutien scolaire / formation", "Services", "tutoring", "Nachhilfe", "academia clases particulares", "ripetizioni", "explicações", "bijles"),
    # --- Tourisme & loisirs ---
    _s("hotel", "Hôtel", "Tourisme & loisirs", "hotel", "Hotel", "hotel", "hotel", "hotel", "hotel"),
    _s("chambre_hotes", "Chambre d'hôtes / gîte", "Tourisme & loisirs", "bed and breakfast", "Pension", "casa rural", "bed and breakfast", "alojamento local", "bed and breakfast"),
    _s("camping", "Camping", "Tourisme & loisirs", "campground", "Campingplatz", "camping", "campeggio", "parque de campismo", "camping"),
    _s("agence_voyage", "Agence de voyage", "Tourisme & loisirs", "travel agency", "Reisebüro", "agencia de viajes", "agenzia di viaggi", "agência de viagens", "reisbureau"),
    _s("location_salle", "Location de salle / événementiel", "Tourisme & loisirs", "event venue", "Eventlocation", "salón de eventos", "sala eventi", "salão de eventos", "evenementenlocatie"),
    _s("ecole_musique_danse", "École de musique / danse", "Tourisme & loisirs", "music school", "Musikschule", "escuela de música", "scuola di musica", "escola de música", "muziekschool"),
    # --- Industrie & agriculture ---
    _s("exploitation_agricole", "Exploitation agricole / ferme", "Industrie & agriculture", "farm", "Bauernhof", "granja", "azienda agricola", "quinta agrícola", "boerderij"),
    _s("vigneron", "Vigneron / domaine viticole", "Industrie & agriculture", "winery", "Weingut", "bodega", "cantina vinicola", "adega", "wijnmakerij"),
    _s("atelier_mecanique", "Atelier de mécanique / usinage", "Industrie & agriculture", "machine shop", "Metallbau", "taller de mecanizado", "officina meccanica di precisione", "oficina de metalomecânica", "metaalbewerking"),
    _s("transport_logistique", "Transport / logistique", "Industrie & agriculture", "trucking company", "Spedition", "empresa de transporte", "autotrasporti", "empresa de transportes", "transportbedrijf"),
]

SECTOR_BY_KEY: dict[str, Sector] = {s.key: s for s in SECTORS}
CATEGORIES: list[str] = list(dict.fromkeys(s.category for s in SECTORS))
