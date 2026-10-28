"""
CRIPTO BREAKER - Rompedor de cifrados clasicos (version 6.3)
Rompe: Cesar, Vigenere, sustitucion simple y XOR.
Mejora v6.3: MIN_LETRAS_VIGENERE reducido de 100 a 60.
Incluye advertencia cuando la confianza es baja.
"""

import re
import math
import random
from collections import Counter, defaultdict


# ============================================================
# CONSTANTES
# ============================================================

FRECUENCIA_ESPANOL = {
    'e': 13.68, 'a': 12.53, 'o': 8.68, 's': 7.98, 'r': 6.87,
    'n': 6.71, 'i': 6.18, 'd': 5.86, 'l': 4.96, 'c': 4.68,
    't': 4.63, 'u': 3.93, 'm': 3.15, 'p': 2.51, 'b': 1.42,
    'g': 1.01, 'v': 0.90, 'y': 0.90, 'q': 0.88, 'h': 0.70,
    'f': 0.69, 'z': 0.52, 'j': 0.44, 'x': 0.22, 'k': 0.11,
    'w': 0.02,
}

PALABRAS_COMUNES = {
    'el', 'la', 'de', 'que', 'y', 'en', 'un', 'ser', 'se', 'no',
    'haber', 'por', 'con', 'su', 'para', 'como', 'estar', 'tener',
    'le', 'lo', 'todo', 'pero', 'mas', 'hacer', 'o', 'poder', 'decir',
    'este', 'ir', 'otro', 'ese', 'si', 'me', 'ya', 'ver', 'porque',
    'dar', 'cuando', 'muy', 'sin', 'vez', 'mucho', 'saber', 'que',
    'sobre', 'mi', 'alguno', 'mismo', 'yo', 'tambien', 'hasta', 'ano',
    'dos', 'querer', 'entre', 'asi', 'primero', 'desde', 'grande',
    'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella', 'si',
    'dia', 'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
    'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde', 'ahora',
    'parte', 'despues', 'vida', 'quedar', 'siempre', 'creer', 'hablar',
    'llevar', 'dejar', 'nada', 'cada', 'seguir', 'menos', 'nuevo',
    'encontrar', 'otro', 'tal', 'solo', 'escribir', 'mundo', 'traves',
    'los', 'las', 'del', 'una', 'unos', 'unas', 'es', 'son',
    'fue', 'han', 'hay', 'ha', 'he', 'has', 'hemos', 'esta', 'estan',
    'estoy', 'estamos', 'era', 'eran', 'fui', 'sea', 'sean',
}

MIN_LETRAS_CESAR = 5
MIN_LETRAS_VIGENERE = 60        # antes 100
MIN_LETRAS_SUSTITUCION = 80
MIN_BYTES_XOR = 50


# ============================================================
# VALIDACION DE ENTRADA
# ============================================================

def validar_entrada(texto):
    if texto is None:
        return False, "El texto es None (vacio)."
    if isinstance(texto, bytes):
        if len(texto) < MIN_BYTES_XOR:
            return False, (f"El texto binario tiene solo {len(texto)} bytes. "
                           f"XOR necesita al menos {MIN_BYTES_XOR} para funcionar.")
        return True, ""
    if not isinstance(texto, str):
        return False, f"Tipo no soportado: {type(texto).__name__}"
    if not texto.strip():
        return False, "El texto esta vacio."
    letras = [c for c in texto if c.isalpha()]
    if len(letras) < MIN_LETRAS_CESAR:
        return False, (f"El texto tiene solo {len(letras)} letras. "
                       f"Necesito al menos {MIN_LETRAS_CESAR} para empezar.")
    return True, ""


# ============================================================
# PUNTUACION
# ============================================================

def puntuar_texto(texto):
    if not texto:
        return -999999
    texto_lower = texto.lower()
    letras = [c for c in texto_lower if c.isalpha()]
    if len(letras) < 5:
        return -999999

    conteo = Counter(letras)
    total = len(letras)
    chi2 = 0.0
    for letra, freq_esperada in FRECUENCIA_ESPANOL.items():
        observado = conteo.get(letra, 0)
        esperado = freq_esperada * total / 100.0
        if esperado > 0:
            chi2 += ((observado - esperado) ** 2) / esperado
    puntaje_freq = -chi2 / 1000.0

    palabras = re.findall(r'[a-z]+', texto_lower)
    matches = sum(1 for p in palabras if p in PALABRAS_COMUNES)
    puntaje_palabras = (matches / max(1, len(palabras))) * 100

    proporcion_espacios = texto.count(' ') / max(1, len(texto))
    if 0.10 < proporcion_espacios < 0.25:
        puntaje_estructura = 20
    elif 0.05 < proporcion_espacios < 0.30:
        puntaje_estructura = 10
    else:
        puntaje_estructura = -10

    return puntaje_freq + puntaje_palabras + puntaje_estructura


def puntuar_por_ngramas(texto, n=2):
    texto_lower = texto.lower()
    bigramas_comunes = ['de', 'la', 'el', 'en', 'qu', 'ue', 'os', 'as',
                        'es', 'er', 'ar', 'ir', 'on', 'an', 're', 'co',
                        'na', 'ra', 'ta', 'ci', 'te', 'se', 'lo', 'le',
                        'do', 'ro', 'po', 'mo', 'no', 'to', 'ca', 'pa']
    conteo = Counter(texto_lower[i:i+n] for i in range(len(texto_lower)-n+1))
    score = sum(conteo[bg] for bg in bigramas_comunes)
    return score / max(1, len(texto_lower) - n + 1) * 100


def puntuar_completo(texto):
    return puntuar_texto(texto) + puntuar_por_ngramas(texto)


# ============================================================
# PUNTUACION ESPECIFICA PARA XOR
# ============================================================

def puntuar_xor_texto(texto):
    if not texto or len(texto) < 10:
        return -999999
    imprimibles = sum(1 for c in texto if c.isprintable() or c in '\n\r\t ')
    proporcion = imprimibles / len(texto)
    if proporcion < 0.90:
        return -999999
    score = proporcion * 200
    texto_lower = texto.lower()
    palabras = re.findall(r'[a-z]+', texto_lower)
    if not palabras:
        return -999999
    matches = sum(1 for p in palabras if p in PALABRAS_COMUNES)
    score += (matches / len(palabras)) * 500
    letras = [c for c in texto_lower if c.isalpha()]
    if len(letras) >= 10:
        conteo = Counter(letras)
        total = len(letras)
        chi2 = 0.0
        for letra, freq_esp in FRECUENCIA_ESPANOL.items():
            obs = conteo.get(letra, 0)
            esp = freq_esp * total / 100.0
            if esp > 0:
                chi2 += ((obs - esp) ** 2) / esp
        score += -chi2 / 50.0
    bigramas = ['de', 'la', 'el', 'en', 'qu', 'ue', 'os', 'as', 'es',
                'er', 'ar', 'ir', 'on', 'an', 're', 'co', 'na', 'ra',
                'ta', 'ci', 'te', 'se', 'lo', 'le', 'do', 'ro', 'po',
                'mo', 'no', 'to', 'ca', 'pa']
    cont_bg = Counter(texto_lower[i:i+2] for i in range(len(texto_lower)-1))
    score += sum(cont_bg[bg] for bg in bigramas) / max(1, len(texto_lower)) * 100
    return score


# ============================================================
# CESAR
# ============================================================

def descifrar_cesar(texto, desplazamiento):
    resultado = []
    for c in texto:
        if c.isalpha():
            base = ord('a') if c.islower() else ord('A')
            nueva = (ord(c) - base - desplazamiento) % 26 + base
            resultado.append(chr(nueva))
        else:
            resultado.append(c)
    return ''.join(resultado)


def romper_cesar(texto_cifrado):
    mejor_score = -float('inf')
    mejor_texto = ""
    mejor_desplazamiento = 0
    for desplazamiento in range(26):
        candidato = descifrar_cesar(texto_cifrado, desplazamiento)
        score = puntuar_completo(candidato)
        if score > mejor_score:
            mejor_score = score
            mejor_texto = candidato
            mejor_desplazamiento = desplazamiento
    return {
        'metodo': 'Cesar',
        'desplazamiento': mejor_desplazamiento,
        'texto': mejor_texto,
        'score': mejor_score,
    }


# ============================================================
# VIGENERE
# ============================================================

def _letras_solo(texto):
    return ''.join(c.lower() for c in texto if c.isalpha())


def indice_coincidencia(texto):
    letras = _letras_solo(texto)
    n = len(letras)
    if n < 2:
        return 0
    conteo = Counter(letras)
    suma = sum(f * (f - 1) for f in conteo.values())
    return suma / (n * (n - 1))


def estimar_longitud_clave(texto_cifrado, max_longitud=20):
    texto = _letras_solo(texto_cifrado)
    if len(texto) < 20:
        return 1, 0.0

    candidatos = []
    for longitud in range(1, min(max_longitud, len(texto) // 3) + 1):
        columnas = [texto[i::longitud] for i in range(longitud)]
        ics = []
        for col in columnas:
            if len(col) > 2:
                ics.append(indice_coincidencia(col))
        if not ics:
            continue
        ic_promedio = sum(ics) / len(ics)
        penalizacion = 1.0 - (longitud / (max_longitud * 3))
        candidatos.append((longitud, ic_promedio * penalizacion))

    if not candidatos:
        return 1, 0.0

    candidatos.sort(key=lambda x: -x[1])

    mejor_final = candidatos[0][0]
    mejor_score_final = -float('inf')

    for longitud, _ in candidatos[:3]:
        texto_letras = _letras_solo(texto_cifrado)
        clave = []
        for pos in range(longitud):
            columna = texto_letras[pos::longitud]
            mejor_score = -float('inf')
            mejor_desp = 0
            for desp in range(26):
                descifrada = ''.join(
                    chr((ord(c) - ord('a') - desp) % 26 + ord('a'))
                    for c in columna
                )
                sc = puntuar_texto(descifrada)
                if sc > mejor_score:
                    mejor_score = sc
                    mejor_desp = desp
            clave.append(mejor_desp)

        descifrado = []
        idx = 0
        for c in texto_cifrado:
            if c.isalpha():
                d = clave[idx % len(clave)]
                base = ord('a') if c.islower() else ord('A')
                descifrado.append(chr((ord(c) - base - d) % 26 + base))
                idx += 1
            else:
                descifrado.append(c)
        score_final = puntuar_texto(''.join(descifrado))
        if score_final > mejor_score_final:
            mejor_score_final = score_final
            mejor_final = longitud

    return mejor_final, 0.0


def romper_vigenere(texto_cifrado):
    longitud, _ = estimar_longitud_clave(texto_cifrado)
    texto_letras = _letras_solo(texto_cifrado)
    clave = []
    for pos in range(longitud):
        columna = texto_letras[pos::longitud]
        mejor_score = -float('inf')
        mejor_desplazamiento = 0
        for desp in range(26):
            descifrada = ''.join(
                chr((ord(c) - ord('a') - desp) % 26 + ord('a'))
                for c in columna
            )
            score = puntuar_texto(descifrada)
            if score > mejor_score:
                mejor_score = score
                mejor_desplazamiento = desp
        clave.append(mejor_desplazamiento)

    resultado = []
    idx_letra = 0
    for c in texto_cifrado:
        if c.isalpha():
            desp = clave[idx_letra % len(clave)]
            base = ord('a') if c.islower() else ord('A')
            nueva = (ord(c) - base - desp) % 26 + base
            resultado.append(chr(nueva))
            idx_letra += 1
        else:
            resultado.append(c)

    return {
        'metodo': 'Vigenere',
        'longitud_clave': longitud,
        'clave_numerica': clave,
        'texto': ''.join(resultado),
        'score': puntuar_completo(''.join(resultado)),
    }


# ============================================================
# SUSTITUCION SIMPLE
# ============================================================

def _frecuencia_ordenada(texto):
    letras = [c.lower() for c in texto if c.isalpha()]
    conteo = Counter(letras)
    return [letra for letra, _ in conteo.most_common()]


def romper_sustitucion(texto_cifrado, iteraciones=15000):
    orden_espanol = [l for l, _ in sorted(
        FRECUENCIA_ESPANOL.items(), key=lambda x: -x[1]
    )]
    orden_texto = _frecuencia_ordenada(texto_cifrado)

    mapeo = {}
    for i, letra_cifrada in enumerate(orden_texto):
        if i < len(orden_espanol):
            mapeo[letra_cifrada] = orden_espanol[i]
        else:
            mapeo[letra_cifrada] = letra_cifrada

    def aplicar(m):
        return ''.join(
            m.get(c.lower(), c.lower()) if c.isalpha() else c
            for c in texto_cifrado
        )

    mejor_texto = aplicar(mapeo)
    mejor_score = puntuar_completo(mejor_texto)

    letras = list(mapeo.keys())
    for _ in range(iteraciones):
        if len(letras) < 2:
            break
        a, b = random.sample(letras, 2)
        mapeo[a], mapeo[b] = mapeo[b], mapeo[a]
        candidato = aplicar(mapeo)
        score = puntuar_completo(candidato)
        if score > mejor_score:
            mejor_score = score
            mejor_texto = candidato
        else:
            mapeo[a], mapeo[b] = mapeo[b], mapeo[a]

    return {
        'metodo': 'Sustitucion simple',
        'mapeo': mapeo,
        'texto': mejor_texto,
        'score': mejor_score,
    }


# ============================================================
# XOR
# ============================================================

def descifrar_xor_con_clave(texto_cifrado, clave):
    return bytes(
        texto_cifrado[i] ^ clave[i % len(clave)]
        for i in range(len(texto_cifrado))
    )


def puntuar_bytes_xor(bloque):
    try:
        texto = bloque.decode('latin-1')
    except Exception:
        return -999999
    return puntuar_xor_texto(texto)


def romper_xor(texto_cifrado, longitud_clave_max=8):
    if isinstance(texto_cifrado, str):
        texto_cifrado = texto_cifrado.encode('latin-1')

    mejor_global = {'score': -float('inf'), 'texto': '', 'clave': b''}

    for longitud in range(1, longitud_clave_max + 1):
        if len(texto_cifrado) < longitud * 4:
            continue

        top_candidatos_por_pos = []
        for pos in range(longitud):
            bloque = bytes(texto_cifrado[pos::longitud])
            scores_por_k = []
            for k in range(256):
                descifrado = bytes(b ^ k for b in bloque)
                score = puntuar_bytes_xor(descifrado)
                if score > -1000:
                    scores_por_k.append((score, k))
            scores_por_k.sort(reverse=True)
            top_candidatos_por_pos.append([k for _, k in scores_por_k[:3]])

        import itertools
        combinaciones_probadas = 0
        for combo in itertools.product(*top_candidatos_por_pos):
            if combinaciones_probadas >= 200:
                break
            combinaciones_probadas += 1
            clave = bytes(combo)
            descifrado = descifrar_xor_con_clave(texto_cifrado, clave)
            try:
                texto = descifrado.decode('latin-1')
            except Exception:
                continue
            score = puntuar_xor_texto(texto)
            if score > mejor_global['score']:
                mejor_global = {
                    'score': score,
                    'texto': texto,
                    'clave': clave,
                    'longitud': longitud,
                }

    return {
        'metodo': 'XOR',
        'texto': mejor_global['texto'],
        'clave': mejor_global.get('clave', b''),
        'longitud': mejor_global.get('longitud', 0),
        'score': mejor_global['score'],
    }


# ============================================================
# DETECTOR INTELIGENTE
# ============================================================

def detectar_tipo_inteligente(texto, verbose=False):
    es_valido, error = validar_entrada(texto)
    if not es_valido:
        return None, -float('inf'), error

    letras = [c for c in texto if c.isalpha()] if isinstance(texto, str) else []
    n_letras = len(letras)
    resultados = {}

    if n_letras >= MIN_LETRAS_CESAR:
        try:
            resultados['cesar'] = romper_cesar(texto)
        except Exception as e:
            if verbose:
                print(f"  [Cesar] Error: {e}")

    if n_letras >= MIN_LETRAS_VIGENERE:
        try:
            resultados['vigenere'] = romper_vigenere(texto)
        except Exception as e:
            if verbose:
                print(f"  [Vigenere] Error: {e}")

    if n_letras >= MIN_LETRAS_SUSTITUCION:
        try:
            resultados['sustitucion'] = romper_sustitucion(texto, iteraciones=8000)
        except Exception as e:
            if verbose:
                print(f"  [Sustitucion] Error: {e}")

    try:
        if isinstance(texto, str):
            no_imprimibles = sum(
                1 for c in texto if not c.isprintable() and c not in '\n\r\t'
            )
            if no_imprimibles / max(1, len(texto)) > 0.05:
                resultados['xor'] = romper_xor(texto, longitud_clave_max=8)
        else:
            resultados['xor'] = romper_xor(texto, longitud_clave_max=8)
    except Exception as e:
        if verbose:
            print(f"  [XOR] Error: {e}")

    if not resultados:
        return None, -float('inf'), "Ningun rompedor pudo procesar el texto."

    mejor_tipo = None
    mejor_score = -float('inf')
    for tipo, resultado in resultados.items():
        score = resultado.get('score', -float('inf'))
        if verbose:
            preview = resultado.get('texto', '')[:50].replace('\n', ' ')
            print(f"  [{tipo:12s}] score={score:8.2f}  preview: {preview}...")
        if score > mejor_score:
            mejor_score = score
            mejor_tipo = tipo

    detalle = f"Probados: {', '.join(resultados.keys())}. Ganador: {mejor_tipo}"
    return mejor_tipo, mejor_score, detalle


def nivel_confianza(mejor_score):
    if mejor_score > 100:
        return 'alta'
    elif mejor_score > 30:
        return 'media'
    else:
        return 'baja'


def advertencia_por_longitud(texto, tipo):
    """
    Devuelve un mensaje de advertencia si el texto es muy corto
    para el tipo detectado.
    """
    if not isinstance(texto, str):
        return None
    n_letras = len([c for c in texto if c.isalpha()])
    if tipo == 'vigenere' and n_letras < 200:
        return (f"AVISO: el texto tiene {n_letras} letras. Vigenere funciona "
                f"mejor con 200+ letras. El resultado puede ser impreciso.")
    if tipo == 'sustitucion' and n_letras < 150:
        return (f"AVISO: el texto tiene {n_letras} letras. La sustitucion "
                f"funciona mejor con 150+ letras. El resultado puede ser impreciso.")
    return None


# ============================================================
# FUNCION PRINCIPAL
# ============================================================

def romper_automatico(texto_cifrado, tipo=None, verbose=False):
    es_valido, error = validar_entrada(texto_cifrado)
    if not es_valido:
        return {
            'metodo': 'ERROR',
            'texto': '',
            'score': -float('inf'),
            'error': error,
        }

    if tipo is None:
        tipo, score, detalle = detectar_tipo_inteligente(
            texto_cifrado, verbose=verbose
        )
        if tipo is None:
            return {
                'metodo': 'ERROR',
                'texto': '',
                'score': -float('inf'),
                'error': detalle,
            }
        confianza = nivel_confianza(score)
        print(f"[Detector inteligente] Tipo: {tipo} (confianza: {confianza})")
        if verbose:
            print(f"[Detector] {detalle}")

    if tipo == 'cesar':
        resultado = romper_cesar(texto_cifrado)
    elif tipo == 'vigenere':
        resultado = romper_vigenere(texto_cifrado)
    elif tipo == 'sustitucion':
        resultado = romper_sustitucion(texto_cifrado)
    elif tipo == 'xor':
        resultado = romper_xor(texto_cifrado)
    else:
        return {
            'metodo': 'ERROR',
            'texto': '',
            'score': -float('inf'),
            'error': f"Tipo desconocido: {tipo}",
        }

    # Anadir advertencia si aplica
    advertencia = advertencia_por_longitud(texto_cifrado, tipo)
    if advertencia:
        resultado['advertencia'] = advertencia

    return resultado


# ============================================================
# CIFRADORES
# ============================================================

def cifrar_cesar(texto, desplazamiento):
    resultado = []
    for c in texto:
        if c.isalpha():
            base = ord('a') if c.islower() else ord('A')
            nueva = (ord(c) - base + desplazamiento) % 26 + base
            resultado.append(chr(nueva))
        else:
            resultado.append(c)
    return ''.join(resultado)


def cifrar_vigenere(texto, clave):
    resultado = []
    idx = 0
    for c in texto:
        if c.isalpha():
            desp = ord(clave[idx % len(clave)].lower()) - ord('a')
            base = ord('a') if c.islower() else ord('A')
            nueva = (ord(c) - base + desp) % 26 + base
            resultado.append(chr(nueva))
            idx += 1
        else:
            resultado.append(c)
    return ''.join(resultado)


# ============================================================
# PUNTO DE ENTRADA (CLI)
# ============================================================

if __name__ == "__main__":
    print("Cripto Breaker 6.3")
    print("Pega un texto cifrado o escribe 'salir':")
    try:
        while True:
            entrada = input("\nTexto cifrado: ").strip()
            if entrada.lower() == 'salir' or not entrada:
                print("Hasta pronto, socio!")
                break
            resultado = romper_automatico(entrada, verbose=True)
            if resultado.get('metodo') == 'ERROR':
                print(f"Error: {resultado.get('error', 'desconocido')}")
                continue
            print(f"\nMetodo detectado: {resultado['metodo']}")
            print(f"Texto descifrado: {resultado['texto']}")
            if 'advertencia' in resultado:
                print(f"Advertencia: {resultado['advertencia']}")
    except (KeyboardInterrupt, EOFError):
        print("\nHasta pronto, socio!")