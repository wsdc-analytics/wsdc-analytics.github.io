import re
from pathlib import Path

# --- Configuration ---
EN_FILE = Path('dancers_2025_en.html')
ES_FILE = Path('dancers_2025_es.html')

# --- Translations Data ---

# English Translations for Dancer Highlights
EN_HIGHLIGHTS = {
    # Global
    "Zachary Skinner": """<div class="highlight-insight" style="margin-top: 32px;">
<p><strong>Zachary Skinner</strong> - the brightest dancer of the year! Absolute leader by wins (14 first places), earned points at 17 events, was equally successful as both leader and follower. Demonstrated exceptionally high win rate: 9 in All-Stars as leader, 5 in Advanced as follower.</p>
<p><strong>Geography:</strong> won in all regions of the world - Europe (five wins), Australia (five wins), Asia (two wins) and North America (two wins), which is a completely unique achievement.</p>
<p><strong>Most successful event:</strong> BudaFest - 28 points.</p>
</div>""",
    "Igor Pitangui": """<div class="highlight-insight">
<p><strong>Igor Pitangui</strong> - achieved a unique feat: the only one in the top who won in both Champions division (one win as follower) and All-Stars in both roles (four wins as follower, two wins as leader). Total seven wins, earned points at 19 events, demonstrating versatility at the highest level.</p>
<p><strong>Geography:</strong> 81.8% points earned at European events, all seven wins achieved in Europe.</p>
<p><strong>Most successful event:</strong> unique achievement at Autumn Swing Challenge: won two senior divisions at one event - Champions (follower) and All-Stars (leader).</p>
</div>""",
    "Kristen Wallace": """<div class="highlight-insight">
<p><strong>Kristen Wallace</strong> - leader by points earned and by number of events with points: earned points at 23 events in three divisions, competing in both roles (20 times as follower in All-Stars, 16 times as leader in Advanced, 1 time as leader in Intermediate), achieving five wins.</p>
<p><strong>Geography:</strong> 99.4% points and all 5 wins at American events.</p>
<p><strong>Most successful event:</strong> Boogie By The Bay - 25 points.</p>
</div>""",
    "Nicole Ramirez": """<div class="highlight-insight">
<p><strong>Nicole Ramirez</strong> - absolute dominance in Champions: leader by both points (61) and wins (10), earned and won at 15 events.</p>
<p><strong>Geography:</strong> 82.0% points earned at American events; wins: seven in USA, three in Europe.</p>
<p><strong>Most successful event:</strong> Boogie By The Bay - 10 points.</p>
</div>""",
    "Aleksandra Radziejewska": """<div class="highlight-insight">
<p><strong>Aleksandra Radziejewska</strong> - impressive result in Advanced: 6 wins out of 9 participations as follower, as a result 2nd place by points earned in this division in 2025 (73). Also earned points in All-Stars at one more event.</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> Warsaw Halloween Swing - 15 points.</p>
</div>""",
    "Hanna Junk": """<div class="highlight-insight">
<p><strong>Hanna Junk</strong> - greatest diversity of divisions in the top: earned points in four divisions (Novice, Intermediate, Advanced, All-Stars) at 15 events and achieved four wins in Advanced. Showed effective growth as follower: closed Intermediate and Advanced and earned first All-Stars points as follower, while also successfully competing as leader in Intermediate (6 events with points).</p>
<p><strong>Geography:</strong> 86.5% points earned at European events (three wins), 13.5% in North America (one win).</p>
<p><strong>Most successful event:</strong> Paris Westie Fest - 17 points.</p>
</div>""",
    "Mathias Mendillo": """<div class="highlight-insight">
<p><strong>Mathias Mendillo</strong> - another example of impressive progress: starting in January in Intermediate, managed to close Advanced and earn points in All-Stars during 2025, earning a total of 104 points and achieving four wins. One of the fastest-growing dancers across divisions in 2025.</p>
<p><strong>Geography:</strong> 94.2% points earned at American events, all four wins in USA.</p>
<p><strong>Most successful events:</strong> Wild Wild Westie, Novice Invitational and USA Grand Nationals - 15 points each.</p>
</div>""",
    "Sebastian Quinones": """<div class="highlight-insight">
<p><strong>Sebastian Quinones</strong> - absolute leader by points in All-Stars: earned 105 points in this division as leader (21 events, six wins), which constitutes the main part of his result (125 points total).</p>
<p><strong>Geography:</strong> 99.2% points earned at American events, all seven wins in USA.</p>
<p><strong>Most successful event:</strong> Novice Invitational - 18 points.</p>
</div>""",
    "Mackenzie Keister": """<div class="highlight-insight">
<p><strong>Mackenzie Keister</strong> - second by points in All-Stars: earned 104 points in this division as follower (21 events, five wins), showing high performance and consistent results, successfully debuted at The Open in Showcase.</p>
<p><strong>Geography:</strong> all 104 points and all five wins achieved at American events.</p>
<p><strong>Most successful events:</strong> The Open and The After Party - 15 points each.</p>
</div>""",
    "Keerigan Rudd": """<div class="highlight-insight">
<p><strong>Keerigan Rudd</strong> - third by points in All-Stars as leader: 100 points in All-Stars (17 events, five wins) plus 5 points in Champions. Maintains consistently high level: in 2024 earned 140 points in All-Stars with 13 wins at 28 events, demonstrating enviable consistency and high results.</p>
<p><strong>Geography:</strong> 95.2% points earned at American events, and also won once in Australia.</p>
<p><strong>Most successful event:</strong> Wild Wild Westie - 15 points.</p>
</div>""",

    # European
    "Charlie Fournier": """<div class="highlight-insight" style="margin-top: 32px;">
<p><strong>Charlie Fournier</strong> - amazing achievement from a young girl (celebrated a win in Juniors in November), who placed 2nd by points at European events. Competed exclusively at French events in Intermediate and Advanced as follower and in Intermediate as leader, demonstrating consistently high results. Earned points at 10 events, achieved two wins.</p>
<p><strong>Geography:</strong> all 96 points earned at French events.</p>
<p><strong>Most successful event:</strong> Rolling Swing - 23 points.</p>
</div>""",
    "Allan Thivoz": """<div class="highlight-insight">
<p><strong>Allan Thivoz</strong> - leader by wins at European events in All-Stars division (6), marked a unique achievement by winning at three consecutive events over 3 weeks in October and November 2025. Earned 55 points at 10 European events.</p>
<p><strong>Geography:</strong> 98.2% points earned at European events.</p>
<p><strong>Most successful event:</strong> Scandinavian Open - 10 points.</p>
</div>""",
    "Joshua Schubert": """<div class="highlight-insight">
<p><strong>Joshua Schubert</strong> - 2nd place by number of events with points (17) at European events. All points earned in the highest All-Stars division, placing 3rd by this metric. Also successfully debuted at The Open in Classic division.</p>
<p><strong>Geography:</strong> 98.3% points earned at European events.</p>
<p><strong>Most successful event:</strong> Swingtzerland - 10 points.</p>
</div>""",
    "Florian Hamm": """<div class="highlight-insight">
<p><strong>Florian Hamm</strong> - 2nd place by points earned in All-Stars division (79) at European events and tied 3rd place by events with points (16), and also achieved three wins.</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> Bavarian Open - 10 points.</p>
</div>""",
    "Clement Turpain": """<div class="highlight-insight">
<p><strong>Clement Turpain</strong> - 5th place by points at European events (86). Versatile dancer: earned points in Advanced as follower and in All-Stars as leader, achieving three wins. Also won once at The Open in Advanced as follower.</p>
<p><strong>Geography:</strong> 84.3% points earned at European events, 14.7% at American events.</p>
<p><strong>Most successful event:</strong> Warsaw Halloween Swing - 22 points.</p>
</div>""",
    "Sebastian Gerwald": """<div class="highlight-insight">
<p><strong>Sebastian Gerwald</strong> - tied 2nd place by wins (6). One of 5 dancers who earned points in All-Stars division in both leader and follower roles in 2025 at European events.</p>
<p><strong>Geography:</strong> all points earned at European events (14).</p>
<p><strong>Most successful event:</strong> Baltic Swing - 16 points.</p>
</div>""",
    "Stefanie Tschom": """<div class="highlight-insight">
<p><strong>Stefanie Tschom</strong> - leads by points in All-Stars division among followers (72) and ties 3rd place by number of events with points at European events (16). Achieved five wins, which is also the best result for followers.</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> Finnfest and King Swing - 10 points each.</p>
</div>""",
    "Alexa Partos": """<div class="highlight-insight">
<p><strong>Alexa Partos</strong> - 3rd place by points at European events (91). Successfully combined performances as follower in Intermediate (1) and Advanced (8) and as leader in Novice (1) and Intermediate (5). Earned points at 10 European events, achieved one win.</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> BudaFest - 22 points.</p>
</div>""",

    # Sophisticated
    "Chloe Winzar": """<div class="highlight-insight" style="margin-top: 32px;">
<p><strong>Chloe Winzar</strong> - leader by points in Sophisticated (94) and tied 3rd place by wins (4). Earned points at 13 events.</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> Nordic WCS Championships - 15 points.</p>
</div>""",
    "Haley Hauglum": """<div class="highlight-insight">
<p><strong>Haley Hauglum</strong> - 2nd place by points (91) and 2nd place by wins (5) among Sophisticated dancers. Earned points at 14 events.</p>
<p><strong>Geography:</strong> 91.4% points earned at American events, 8.6% at European events.</p>
<p><strong>Most successful event:</strong> USA Grand Nationals - 18 points.</p>
</div>""",
    "Marine Monin": """<div class="highlight-insight">
<p><strong>Marine Monin</strong> - 3rd place by points (87) and tied 3rd place by wins (4). Earned points at 11 events.</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> UK WCS Championships - 15 points.</p>
</div>""",
    "Stanley Seguy": """<div class="highlight-insight">
<p><strong>Stanley Seguy</strong> - leader by wins in Sophisticated (6) and tied 4th place by points (81). Earned points at 9 events, showing high performance: six wins out of nine events.</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> BudaFest - 15 points.</p>
</div>""",
    "Jerome Fernandez": """<div class="highlight-insight">
<p><strong>Jerome Fernandez</strong> - tied 4th place by points (81) and 3rd place by events (14). Achieved two wins. Won in two regions - Europe and Asia.</p>
<p><strong>Geography:</strong> 93.3% points earned at European events, 6.7% at other events.</p>
<p><strong>Most successful event:</strong> Korean Open WCS Championships - 15 points.</p>
</div>""",
    "Jerome Tangha": """<div class="highlight-insight">
<p><strong>Jerome Tangha</strong> - leader by number of events with points (15, tied 1st place with Lucie Renaud), 7th place by points (78) and tied 3rd place by wins (4).</p>
<p><strong>Geography:</strong> all points earned at European events.</p>
<p><strong>Most successful event:</strong> WCS Festival - 12 points.</p>
</div>""",
}

# Spanish Translations for Dancer Highlights
ES_HIGHLIGHTS = {
    # Global
    "Zachary Skinner": """<div class="highlight-insight" style="margin-top: 32px;">
<p><strong>Zachary Skinner</strong> - ¡el bailarín más destacado del año! Líder absoluto por victorias (14 primeros lugares), obtuvo puntos en 17 eventos, fue igualmente exitoso como líder y seguidor. Demostró un porcentaje de victorias excepcionalmente alto: 9 en All-Stars como líder, 5 en Advanced como seguidor.</p>
<p><strong>Geografía:</strong> ganó en todas las regiones del mundo - Europa (cinco victorias), Australia (cinco victorias), Asia (dos victorias) y América del Norte (dos victorias), lo cual es un logro completamente único.</p>
<p><strong>Evento más exitoso:</strong> BudaFest - 28 puntos.</p>
</div>""",
    "Igor Pitangui": """<div class="highlight-insight">
<p><strong>Igor Pitangui</strong> - logró una hazaña única: el único en el top que ganó tanto en la división Champions (una victoria como seguidor) como en All-Stars en ambos roles (cuatro victorias como seguidor, dos victorias como líder). Total siete victorias, obtuvo puntos en 19 eventos, demostrando versatilidad al más alto nivel.</p>
<p><strong>Geografía:</strong> 81.8% puntos obtenidos en eventos europeos, todas las siete victorias logradas en Europa.</p>
<p><strong>Evento más exitoso:</strong> logro único en Autumn Swing Challenge: ganó dos divisiones senior en un evento - Champions (seguidor) y All-Stars (líder).</p>
</div>""",
    "Kristen Wallace": """<div class="highlight-insight">
<p><strong>Kristen Wallace</strong> - líder por puntos obtenidos y por número de eventos con puntos: obtuvo puntos en 23 eventos en tres divisiones, compitiendo en ambos roles (20 veces como seguidor en All-Stars, 16 veces como líder en Advanced, 1 vez como líder en Intermediate), logrando cinco victorias.</p>
<p><strong>Geografía:</strong> 99.4% puntos y todas las 5 victorias en eventos americanos.</p>
<p><strong>Evento más exitoso:</strong> Boogie By The Bay - 25 puntos.</p>
</div>""",
    "Nicole Ramirez": """<div class="highlight-insight">
<p><strong>Nicole Ramirez</strong> - dominio absoluto en Champions: líder tanto por puntos (61) como por victorias (10), obtenidos y ganados en 15 eventos.</p>
<p><strong>Geografía:</strong> 82.0% puntos obtenidos en eventos americanos; victorias: siete en EE.UU., tres en Europa.</p>
<p><strong>Evento más exitoso:</strong> Boogie By The Bay - 10 puntos.</p>
</div>""",
    "Aleksandra Radziejewska": """<div class="highlight-insight">
<p><strong>Aleksandra Radziejewska</strong> - resultado impresionante en Advanced: 6 victorias de 9 participaciones como seguidor, como resultado 2do lugar por puntos obtenidos en esta división en 2025 (73). También obtuvo puntos en All-Stars en un evento más.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> Warsaw Halloween Swing - 15 puntos.</p>
</div>""",
    "Hanna Junk": """<div class="highlight-insight">
<p><strong>Hanna Junk</strong> - mayor diversidad de divisiones en el top: obtuvo puntos en cuatro divisiones (Novice, Intermediate, Advanced, All-Stars) en 15 eventos y logró cuatro victorias en Advanced. Mostró crecimiento efectivo como seguidor: cerró Intermediate y Advanced y obtuvo los primeros puntos de All-Stars como seguidor, mientras también competía exitosamente como líder en Intermediate (6 eventos con puntos).</p>
<p><strong>Geografía:</strong> 86.5% puntos obtenidos en eventos europeos (tres victorias), 13.5% en América del Norte (una victoria).</p>
<p><strong>Evento más exitoso:</strong> Paris Westie Fest - 17 puntos.</p>
</div>""",
    "Mathias Mendillo": """<div class="highlight-insight">
<p><strong>Mathias Mendillo</strong> - otro ejemplo de progreso impresionante: comenzando en enero en Intermediate, logró cerrar Advanced y obtener puntos en All-Stars durante 2025, obteniendo un total de 104 puntos y logrando cuatro victorias. Uno de los bailarines de más rápido crecimiento entre divisiones en 2025.</p>
<p><strong>Geografía:</strong> 94.2% puntos obtenidos en eventos americanos, todas las cuatro victorias en EE.UU.</p>
<p><strong>Eventos más exitosos:</strong> Wild Wild Westie, Novice Invitational y USA Grand Nationals - 15 puntos cada uno.</p>
</div>""",
    "Sebastian Quinones": """<div class="highlight-insight">
<p><strong>Sebastian Quinones</strong> - líder absoluto por puntos en All-Stars: obtuvo 105 puntos en esta división como líder (21 eventos, seis victorias), lo que constituye la mayor parte de su resultado (125 puntos en total).</p>
<p><strong>Geografía:</strong> 99.2% puntos obtenidos en eventos americanos, todas las siete victorias en EE.UU.</p>
<p><strong>Evento más exitoso:</strong> Novice Invitational - 18 puntos.</p>
</div>""",
    "Mackenzie Keister": """<div class="highlight-insight">
<p><strong>Mackenzie Keister</strong> - segunda por puntos en All-Stars: obtuvo 104 puntos en esta división como seguidor (21 eventos, cinco victorias), mostrando alto rendimiento y resultados consistentes, debutó exitosamente en The Open en Showcase.</p>
<p><strong>Geografía:</strong> todos los 104 puntos y todas las cinco victorias logradas en eventos americanos.</p>
<p><strong>Eventos más exitosos:</strong> The Open y The After Party - 15 puntos cada uno.</p>
</div>""",
    "Keerigan Rudd": """<div class="highlight-insight">
<p><strong>Keerigan Rudd</strong> - tercero por puntos en All-Stars como líder: 100 puntos en All-Stars (17 eventos, cinco victorias) más 5 puntos en Champions. Mantiene un nivel consistentemente alto: en 2024 obtuvo 140 puntos en All-Stars con 13 victorias en 28 eventos, demostrando constancia envidiable y altos resultados.</p>
<p><strong>Geografía:</strong> 95.2% puntos obtenidos en eventos americanos, y también ganó una vez en Australia.</p>
<p><strong>Evento más exitoso:</strong> Wild Wild Westie - 15 puntos.</p>
</div>""",

    # European
    "Charlie Fournier": """<div class="highlight-insight" style="margin-top: 32px;">
<p><strong>Charlie Fournier</strong> - logro sorprendente de una joven (celebrada con una victoria en Juniors en noviembre), que ocupó el 2do lugar por puntos en eventos europeos. Compitió exclusivamente en eventos franceses en Intermediate y Advanced como seguidor y en Intermediate como líder, demostrando resultados consistentemente altos. Obtuvo puntos en 10 eventos, logró dos victorias.</p>
<p><strong>Geografía:</strong> todos los 96 puntos obtenidos en eventos franceses.</p>
<p><strong>Evento más exitoso:</strong> Rolling Swing - 23 puntos.</p>
</div>""",
    "Allan Thivoz": """<div class="highlight-insight">
<p><strong>Allan Thivoz</strong> - líder por victorias en eventos europeos en la división All-Stars (6), marcó un logro único ganando en tres eventos consecutivos durante 3 semanas en octubre y noviembre de 2025. Obtuvo 55 puntos en 10 eventos europeos.</p>
<p><strong>Geografía:</strong> 98.2% puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> Scandinavian Open - 10 puntos.</p>
</div>""",
    "Joshua Schubert": """<div class="highlight-insight">
<p><strong>Joshua Schubert</strong> - 2do lugar por número de eventos con puntos (17) en eventos europeos. Todos los puntos obtenidos en la división más alta All-Stars, ocupando el 3er lugar por esta métrica. También debutó exitosamente en The Open en la división Classic.</p>
<p><strong>Geografía:</strong> 98.3% puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> Swingtzerland - 10 puntos.</p>
</div>""",
    "Florian Hamm": """<div class="highlight-insight">
<p><strong>Florian Hamm</strong> - 2do lugar por puntos obtenidos en la división All-Stars (79) en eventos europeos y empató el 3er lugar por eventos con puntos (16), y también logró tres victorias.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> Bavarian Open - 10 puntos.</p>
</div>""",
    "Clement Turpain": """<div class="highlight-insight">
<p><strong>Clement Turpain</strong> - 5to lugar por puntos en eventos europeos (86). Bailarín versátil: obtuvo puntos en Advanced como seguidor y en All-Stars como líder, logrando tres victorias. También ganó una vez en The Open en Advanced como seguidor.</p>
<p><strong>Geografía:</strong> 84.3% puntos obtenidos en eventos europeos, 14.7% en eventos americanos.</p>
<p><strong>Evento más exitoso:</strong> Warsaw Halloween Swing - 22 puntos.</p>
</div>""",
    "Sebastian Gerwald": """<div class="highlight-insight">
<p><strong>Sebastian Gerwald</strong> - empató el 2do lugar por victorias (6). Uno de los 5 bailarines que obtuvo puntos en la división All-Stars tanto como líder como seguidor en 2025 en eventos europeos.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos (14).</p>
<p><strong>Evento más exitoso:</strong> Baltic Swing - 16 puntos.</p>
</div>""",
    "Stefanie Tschom": """<div class="highlight-insight">
<p><strong>Stefanie Tschom</strong> - lidera por puntos en la división All-Stars entre seguidores (72) y empata el 3er lugar por número de eventos con puntos en eventos europeos (16). Logró cinco victorias, lo cual también es el mejor resultado para seguidores.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> Finnfest y King Swing - 10 puntos cada uno.</p>
</div>""",
    "Alexa Partos": """<div class="highlight-insight">
<p><strong>Alexa Partos</strong> - 3er lugar por puntos en eventos europeos (91). Combinó exitosamente participaciones como seguidor en Intermediate (1) y Advanced (8) y como líder en Novice (1) e Intermediate (5). Obtuvo puntos en 10 eventos europeos, logró una victoria.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> BudaFest - 22 puntos.</p>
</div>""",

    # Spanish
    "Fran Vidal": """<div class="highlight-insight" style="margin-top: 32px;">
<p><strong>Fran Vidal</strong> - ¡Bailarín Español del Año! 2do lugar por puntos obtenidos (50), líder por victorias (2) y 2do lugar por eventos (11) entre bailarines españoles. Todos los puntos obtenidos en la división Advanced. Quedó un paso del avance a la división All-Stars.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> Warsaw Halloween Swing - 12 puntos.</p>
</div>""",
    "Alvaro Hilario Garcia": """<div class="highlight-insight">
<p><strong>Alvaro Hilario Garcia</strong> - ¡Bailarín español más activamente progresivo en 2025! 3er lugar por puntos (47), líder absoluto por eventos con puntos (16) y 6to lugar por victorias (1).</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos, 21.3% puntos obtenidos en eventos españoles.</p>
<p><strong>Evento más exitoso:</strong> Mediterranean Open WCS - 10 puntos.</p>
</div>""",
    "Julien Espagnet": """<div class="highlight-insight">
<p><strong>Julien Espagnet</strong> - líder por puntos obtenidos entre bailarines españoles (65) y 4to lugar por eventos (8). Logró una victoria en Intermediate.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos, 27.7% en eventos españoles.</p>
<p><strong>Evento más exitoso:</strong> Arousa Westie Fest - 18 puntos.</p>
</div>""",
    "Aleix Figueras": """<div class="highlight-insight">
<p><strong>Aleix Figueras</strong> - líder por victorias entre bailarines españoles (2, empató el 1er lugar con Fran Vidal), 6to lugar por puntos (28) y 5-6 lugar por eventos (6) entre bailarines españoles.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> Finnfest y Paris Westie Fest - 10 puntos cada uno.</p>
</div>""",
    "Margarita Perepelkina": """<div class="highlight-insight">
<p><strong>Margarita Perepelkina</strong> - 5to lugar por puntos (29), 4to lugar por victorias (1) y 5-6 lugar por eventos (6) entre bailarines españoles.</p>
<p><strong>Geografía:</strong> todos los puntos obtenidos en eventos europeos, 31.0% en eventos españoles.</p>
<p><strong>Evento más exitoso:</strong> Lisbon Westie Fest - 18 puntos.</p>
</div>""",
    "Miquel Menendez": """<div class="highlight-insight">
<p><strong>Miquel Menendez</strong> - 8vo lugar por puntos (23) y 3er lugar por eventos (10) entre bailarines españoles. Todos los puntos obtenidos en la división All-Stars.</p>
<p><strong>Geografía:</strong> 65.2% puntos obtenidos en eventos americanos, 34.8% en eventos europeos.</p>
<p><strong>Evento más exitoso:</strong> The Chicago Classic - 8 puntos.</p>
</div>""",
}

# --- Processing Functions ---

def replace_highlights(content, highlights_dict):
    """Replaces highlight blocks in content with translations based on dancer names."""
    new_content = content
    for dancer_name, translated_block in highlights_dict.items():
        # Regex to find the block for this dancer.
        # Captures: <div class="highlight-insight" ...> ... </div>
        # Looking for dancer name inside strong tag
        pattern = re.compile(
            r'(<div class="highlight-insight"[^>]*>\s*<p><strong>' + re.escape(dancer_name) + r'</strong>.*?(?=</div>)\s*</div>)',
            re.DOTALL
        )
        
        match = pattern.search(new_content)
        if match:
            # Replace the found block with the translated block
            new_content = new_content.replace(match.group(0), translated_block + '\n')
        else:
            print(f"Warning: Could not find highlight block for {dancer_name}")
    return new_content

def replace_headers_and_intro(content, lang):
    """Replaces title and intro text based on language."""
    new_content = content
    
    if lang == 'en':
        # Replace Title
        new_content = new_content.replace(
            '<h1 class="article-title">WSDC 2025: Танцоры</h1>',
            '<h1 class="article-title">WSDC 2025: Dancers</h1>'
        )
        # Replace Subtitle (assuming it might be Russian or English)
        # Note: The file currently has Russian subtitle in RU file, but might have English in EN file (partial).
        # We target the Russian one just in case.
        new_content = new_content.replace(
            '<div class="article-subtitle">Самые успешные танцоры WCS в 2025 году</div>',
            '<div class="article-subtitle">Most successful WCS dancers in 2025</div>'
        )
        
        # Replace Intro
        # Note: The intro might be partially translated or not.
        # We look for the Russian intro text.
        ru_intro_start = 'В этой статье мы рассмотрим'
        en_intro_start = 'In this article, we examine'
        
        if ru_intro_start in new_content:
             # Try to replace the whole intro div content
             # We use a simpler string replacement for the div content if possible
             pass # Logic for full block replacement is tricky with just string replace if content varies.
    
    elif lang == 'es':
        # Replace Title
        new_content = new_content.replace(
            '<h1 class="article-title">WSDC 2025: Танцоры</h1>',
            '<h1 class="article-title">WSDC 2025: Bailarines</h1>'
        )
        new_content = new_content.replace(
            '<div class="article-subtitle">Самые успешные танцоры WCS в 2025 году</div>',
            '<div class="article-subtitle">Los bailarines de WCS más exitosos en 2025</div>'
        )
        new_content = new_content.replace(
            '<div class="article-subtitle">Most successful WCS dancers in 2025</div>', # In case it was already English
            '<div class="article-subtitle">Los bailarines de WCS más exitosos en 2025</div>'
        )

    return new_content

def process_file(source_path, target_path, highlights, lang):
    print(f"Processing {target_path}...")
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found {source_path}")
        return

    # Replace headers and intro
    new_content = replace_headers_and_intro(content, lang)
    
    # Replace highlights
    new_content = replace_highlights(new_content, highlights)
    
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Saved {target_path}")

# --- Execution ---

if __name__ == '__main__':
    # Fix English Version
    process_file(EN_FILE, EN_FILE, EN_HIGHLIGHTS, 'en')
    
    # Fix Spanish Version
    process_file(ES_FILE, ES_FILE, ES_HIGHLIGHTS, 'es')
