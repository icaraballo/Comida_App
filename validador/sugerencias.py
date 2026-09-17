"""Sugerir el valor correcto ante algo fuera de vocabulario.

Sin esto, corregir un vault de seis meses es inviable y el registro se abandona
por fricción (ver fixtures/README.md). El orden de las estrategias importa:

1. Mismo valor mal escrito (acento, mayuscula, espacio) -> se dice exactamente eso.
2. Sinonimo conocido ('oficina' -> 'trabajo').
3. Errata: distancia de edicion corta ('anisedad' -> 'ansiedad').
4. Nada plausible -> se ofrece el vocabulario entero, sin inventar.

Nunca se corrige sola: la sugerencia se imprime, el .md lo cambia la persona (D1).
"""

from __future__ import annotations

from dataclasses import dataclass

from esquema import normalizar, sinonimos, vocabularios

# Motivos, para que quien lee el aviso entienda por que se le propone eso.
ORTOGRAFIA = "ortografia"
SINONIMO = "sinonimo"
ERRATA = "errata"
SIN_IDEA = "sin_idea"


@dataclass(frozen=True)
class Sugerencia:
    motivo: str
    candidatos: tuple[str, ...]

    def texto(self) -> str:
        if self.motivo == SIN_IDEA:
            return "valores validos: " + ", ".join(self.candidatos)
        lista = " o ".join(f"`{c}`" for c in self.candidatos)
        if self.motivo == ORTOGRAFIA:
            return f"se escribe {lista} (minusculas y sin acentos)"
        if self.motivo == SINONIMO:
            return f"quiza {lista}"
        return f"quiza {lista}"


def distancia(a: str, b: str) -> int:
    """Levenshtein. Iterativo por filas: son cadenas cortisimas."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previa = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        actual = [i]
        for j, cb in enumerate(b, start=1):
            actual.append(
                min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + (ca != cb))
            )
        previa = actual
    return previa[-1]


def _umbral(valor: str) -> int:
    """Cuanto se tolera antes de dejar de sugerir.

    Un umbral fijo propone disparates con palabras largas y no propone nada con
    las cortas. Escala: 1 hasta 4 letras, 2 hasta 8, 3 en adelante.
    """
    return max(1, min(3, len(valor) // 4))


def sugerir(valor: object, vocabulario: str) -> Sugerencia | None:
    """Sugerencia para `valor` dentro del vocabulario cerrado `vocabulario`."""
    validos = vocabularios()[vocabulario]
    if not isinstance(valor, str):
        return Sugerencia(SIN_IDEA, validos)

    norma = normalizar(valor)

    # 1. Es el valor bueno, mal escrito.
    if norma in validos:
        return Sugerencia(ORTOGRAFIA, (norma,))

    # 2. Sinonimo documentado.
    propuestos = sinonimos().get(vocabulario, {}).get(norma)
    if propuestos:
        return Sugerencia(SINONIMO, tuple(propuestos))
    if propuestos == ():  # sinonimo que significa "aqui no va nada"
        return Sugerencia(SINONIMO, ())

    # 3. Errata.
    tope = _umbral(norma)
    cercanos = sorted(
        ((distancia(norma, v), v) for v in validos), key=lambda par: (par[0], par[1])
    )
    dentro = [v for d, v in cercanos if d <= tope]
    if dentro:
        return Sugerencia(ERRATA, tuple(dentro[:2]))

    # 4. Nada plausible.
    return Sugerencia(SIN_IDEA, validos)


def sugerir_campo(nombre: object, conocidos: tuple[str, ...]) -> Sugerencia | None:
    """Igual, pero para nombres de campo mal escritos ('emociones_ante')."""
    if not isinstance(nombre, str):
        return Sugerencia(SIN_IDEA, conocidos)
    norma = normalizar(nombre)
    cercanos = sorted((distancia(norma, c), c) for c in conocidos)
    dentro = [c for d, c in cercanos if d <= _umbral(norma)]
    if dentro:
        return Sugerencia(ERRATA, tuple(dentro[:2]))
    return Sugerencia(SIN_IDEA, conocidos)
