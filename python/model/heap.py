"""
MODELO - Max-Heap de moderacion con prioridad dinamica y envejecimiento.
Une heap_moderacion.py y reto3_heap_prioridad_dinamica.py.
"""


class Reporte:
    def __init__(self, id_reporte, gravedad, descripcion):
        self.id_reporte = id_reporte
        self.gravedad = gravedad
        self.descripcion = descripcion


class MaxHeap:
    def __init__(self):
        self.arreglo = []
        self.posicion = {}          # id_reporte -> indice (busqueda O(1))

    def _swap(self, i, j):
        a = self.arreglo
        a[i], a[j] = a[j], a[i]
        self.posicion[a[i].id_reporte] = i
        self.posicion[a[j].id_reporte] = j

    def heapify(self, i):           # hundir (sift-down)
        n = len(self.arreglo)
        while True:
            izq, der, mayor = 2 * i + 1, 2 * i + 2, i
            if izq < n and self.arreglo[izq].gravedad > self.arreglo[mayor].gravedad:
                mayor = izq
            if der < n and self.arreglo[der].gravedad > self.arreglo[mayor].gravedad:
                mayor = der
            if mayor == i:
                break
            self._swap(i, mayor)
            i = mayor

    def _subir(self, i):            # burbujear (swim)
        while i > 0:
            p = (i - 1) // 2
            if self.arreglo[i].gravedad > self.arreglo[p].gravedad:
                self._swap(i, p)
                i = p
            else:
                break

    def construir_heap(self, reportes):
        self.arreglo = list(reportes)
        self.posicion = {r.id_reporte: k for k, r in enumerate(self.arreglo)}
        for i in range(len(self.arreglo) // 2 - 1, -1, -1):
            self.heapify(i)

    def insertar(self, reporte):
        if reporte.id_reporte in self.posicion:
            raise ValueError(f"Ya existe un reporte con ID {reporte.id_reporte}.")
        self.arreglo.append(reporte)
        self.posicion[reporte.id_reporte] = len(self.arreglo) - 1
        self._subir(len(self.arreglo) - 1)

    def extraer_max(self):
        if not self.arreglo:
            return None
        maximo = self.arreglo[0]
        del self.posicion[maximo.id_reporte]
        ultimo = self.arreglo.pop()
        if self.arreglo:
            self.arreglo[0] = ultimo
            self.posicion[ultimo.id_reporte] = 0
            self.heapify(0)
        return maximo

    def cambiar_prioridad(self, id_reporte, nueva):
        if id_reporte not in self.posicion:
            return False
        i = self.posicion[id_reporte]
        anterior = self.arreglo[i].gravedad
        self.arreglo[i].gravedad = nueva
        if nueva > anterior:
            self._subir(i)
        elif nueva < anterior:
            self.heapify(i)
        return True

    def envejecer_todos(self, incremento):
        for r in self.arreglo:
            r.gravedad += incremento
        self.construir_heap(self.arreglo)

    def esta_vacio(self):
        return not self.arreglo

    def pendientes_ordenados(self):
        return sorted(self.arreglo, key=lambda r: r.gravedad, reverse=True)

    def es_heap_valido(self):
        n = len(self.arreglo)
        return all(self.arreglo[(i - 1) // 2].gravedad >= self.arreglo[i].gravedad
                   for i in range(1, n))
