from PIL import Image, ImageTk
import heapq
import tkinter as tk
from tkinter import ttk,messagebox, simpledialog
import networkx as nx
import os
import matplotlib.pyplot as plt
import time
import tracemalloc


class RedeSubestacoes:
    def __init__(self):
        self.grafo = nx.Graph()
        self.demandas = {}

    def adicionar_subestacao(self, nome, carga_ideal, carga_atual):
        self.grafo.add_node(nome, carga_ideal=carga_ideal, carga_atual=carga_atual)
        self.demandas[nome] = {"carga_ideal": carga_ideal, "carga_atual": carga_atual}

    def adicionar_conexao(self, de_sub, para_sub, distancia, carga):
        self.grafo.add_edge(de_sub, para_sub, distancia=distancia, carga=carga)
    
    def visualizar_rede(self, canvas):
        # Obter a posição dos nós para exibir o grafo
        pos = nx.spring_layout(self.grafo)
        
        # Ajuste das coordenadas para o Canvas
        largura = canvas.winfo_width()
        altura = canvas.winfo_height()
        coordenadas = {nodo: (pos[nodo][0] * (largura - 100) + 50, pos[nodo][1] * (altura - 100) + 50) for nodo in pos}

        # Desenhar arestas
        for (u, v) in self.grafo.edges():
            x1, y1 = coordenadas[u]
            x2, y2 = coordenadas[v]
            canvas.create_line(x1, y1, x2, y2, fill="black", width=2)

        # Desenhar nós
        for nodo, (x, y) in coordenadas.items():
            canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill="lightblue", outline="black")
            canvas.create_text(x, y, text=nodo, font=("Arial", 12, "bold"))

    def eh_objetivo(self, no, objetivo):
        return no == objetivo

    def heuristica(self, no, objetivo):
        carga_atual = self.grafo.nodes[no]['carga_atual']
        carga_ideal = self.grafo.nodes[no]['carga_ideal']
        return abs(carga_ideal - carga_atual)

    def busca_custo_uniforme(self, inicio, objetivo):
        start_time = time.perf_counter()  # Iniciar medição de tempo
        tracemalloc.start()       # Iniciar medição de memória
        fila = [(0, inicio, [inicio])]
        visitados = set()
        num_nos_visitados = 0

        while fila:
            custo, no, caminho = heapq.heappop(fila)
            num_nos_visitados += 1
            if self.eh_objetivo(no, objetivo):
                end_time = time.perf_counter()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                return caminho, custo, num_nos_visitados, end_time - start_time, peak / 1024  # Retorna pico de memória em KB

            if no not in visitados:
                visitados.add(no)
                for vizinho in self.grafo[no]:
                    if vizinho not in visitados:
                        distancia = self.grafo[no][vizinho]['distancia']
                        carga = self.grafo[no][vizinho]['carga']
                        custo_total = custo + distancia + carga
                        heapq.heappush(fila, (custo_total, vizinho, caminho + [vizinho]))

        end_time = time.perf_counter()
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, None, num_nos_visitados, end_time - start_time, peak / 1024

    def busca_a_star(self, inicio, objetivo):
        start_time = time.perf_counter()
        tracemalloc.start()
        fila = [(0 + self.heuristica(inicio, objetivo), 0, inicio, [inicio])]
        visitados = set()
        num_nos_visitados = 0

        while fila:
            custo_estimado, custo, no, caminho = heapq.heappop(fila)
            num_nos_visitados += 1
            if self.eh_objetivo(no, objetivo):
                end_time = time.perf_counter()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                print(end_time - start_time)
                return caminho, custo, num_nos_visitados, end_time - start_time, peak / 1024

            if no not in visitados:
                visitados.add(no)
                for vizinho in self.grafo[no]:
                    if vizinho not in visitados:
                        distancia = self.grafo[no][vizinho]['distancia']
                        carga = self.grafo[no][vizinho]['carga']
                        novo_custo = custo + distancia + carga
                        custo_estimado_total = novo_custo + self.heuristica(vizinho, objetivo)
                        heapq.heappush(fila, (custo_estimado_total, novo_custo, vizinho, caminho + [vizinho]))

        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, None, num_nos_visitados, end_time - start_time, peak / 1024

    def profundidade_iterativa(self, inicio, objetivo, limite_maximo=50):
        start_time = time.perf_counter()
        tracemalloc.start()
        for limite in range(1, limite_maximo + 1):
            resultado = self._busca_profundidade_limitada(inicio, objetivo, limite)
            if resultado:
                end_time = time.perf_counter()
                caminho, num_nos_visitados = resultado
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return caminho, num_nos_visitados, end_time - start_time, peak / 1024

        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, None, end_time - start_time, peak / 1024

    def _busca_profundidade_limitada(self, inicio, objetivo, limite):
        stack = [(inicio, [inicio])]
        visitados = set()
        num_nos_visitados = 0

        while stack:
            no, caminho = stack.pop()
            num_nos_visitados += 1
            if self.eh_objetivo(no, objetivo):
                return caminho, num_nos_visitados

            if no not in visitados and len(caminho) <= limite:
                visitados.add(no)
                for vizinho in self.grafo[no]:
                    if vizinho not in visitados:
                        stack.append((vizinho, caminho + [vizinho]))

        return None


class InterfaceGrafica:
    def __init__(self, rede):
        self.rede = rede
        self.window = tk.Tk()
        self.window.title("Gerenciamento de Redes de Subestações")
        self.window.geometry("800x600")
        self.window.resizable(False, False)

        # Estilos
        self.style = ttk.Style(self.window)
        self.style.theme_use('clam')  # Experimente temas como 'clam', 'alt', 'default', 'classic'

        # Cores Personalizadas
        self.window.configure(bg="#f0f0f0")

        # Frame para o Logotipo
        self.header_frame = ttk.Frame(self.window, padding=10)
        self.header_frame.pack(fill='x')

        # Carregar e exibir o logotipo
        logo_path = "edm_logo.png"  # Substitua pelo caminho do seu logotipo
        if os.path.exists(logo_path):
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((150, 100), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_image)
            self.logo_label = ttk.Label(self.header_frame, image=self.logo)
            self.logo_label.pack(side='left')
        else:
            self.logo_label = ttk.Label(self.header_frame, text="LOGO", font=("Arial", 24))
            self.logo_label.pack(side='left')

        # Título
        self.title_label = ttk.Label(self.header_frame, text="Sistema de Gerenciamento de Redes", font=("Helvetica", 18, "bold"))
        self.title_label.pack(side='left', padx=20)

        # Frame Principal
        self.main_frame = ttk.Frame(self.window, padding=20)
        self.main_frame.pack(fill='both', expand=True)

        # Botões de Ação
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(pady=10)

        # Definir Botões com Estilos
        button_style = ttk.Style()
        button_style.configure('TButton', font=('Helvetica', 12), padding=10)

        self.btn_custo_uniforme = ttk.Button(self.buttons_frame, text="Busca Custo Uniforme", command=self.buscar_custo_uniforme)
        self.btn_a_star = ttk.Button(self.buttons_frame, text="Busca A*", command=self.buscar_a_star)
        self.btn_profundidade = ttk.Button(self.buttons_frame, text="Busca Profundidade Iterativa", command=self.buscar_profundidade_iterativa)
        self.btn_visualizar = ttk.Button(self.buttons_frame, text="Visualizar Mapa", command=self.visualizar_mapa)

        # Dispor Botões em Grade
        self.btn_custo_uniforme.grid(row=0, column=0, padx=10, pady=10)
        self.btn_a_star.grid(row=0, column=1, padx=10, pady=10)
        self.btn_profundidade.grid(row=1, column=0, padx=10, pady=10)
        self.btn_visualizar.grid(row=1, column=1, padx=10, pady=10)

        # Canvas para o Mapa
        self.mapa_canvas = tk.Canvas(self.main_frame, bg="white", width=760, height=400)
        self.mapa_canvas.pack(pady=20)
    
    def adicionar_subestacoes_e_conexoes(self):
            # Adiciona subestações de exemplo
        self.rede.adicionar_subestacao("A", 50, 30)
        self.rede.adicionar_subestacao("B", 40, 35)
        self.rede.adicionar_subestacao("C", 60, 5)
        self.rede.adicionar_subestacao("D", 70, 50)
        self.rede.adicionar_subestacao("E", 55, 40)
        self.rede.adicionar_subestacao("F", 65, 60)
        self.rede.adicionar_subestacao("G", 75, 55)
        
        # Adiciona conexões entre as subestações
        self.rede.adicionar_conexao("A", "B", 10, 5)
        self.rede.adicionar_conexao("A", "C", 15, 10)
        self.rede.adicionar_conexao("B", "D", 20, 15)
        self.rede.adicionar_conexao("C", "D", 10, 5)
        self.rede.adicionar_conexao("C", "E", 25, 20)
        self.rede.adicionar_conexao("D", "F", 30, 10)
        self.rede.adicionar_conexao("E", "G", 35, 15)
        self.rede.adicionar_conexao("F", "G", 10, 5)

    def buscar_custo_uniforme(self):
        inicio = simpledialog.askstring("Busca Custo Uniforme", "Informe a subestação de origem:", parent=self.window)
        objetivo = simpledialog.askstring("Busca Custo Uniforme", "Informe a subestação de destino:", parent=self.window)
        if inicio and objetivo:
            caminho, custo, num_nos_visitados, tempo_execucao, memoria = self.rede.busca_custo_uniforme(inicio, objetivo)
            if caminho:
                messagebox.showinfo("Busca Custo Uniforme", f"Caminho: {' -> '.join(caminho)}, Custo: {custo}\n"
                                                            f"Nós Visitados: {num_nos_visitados}\n"
                                                            f"Tempo de Execução: {tempo_execucao:.4f} segundos\n"
                                                            f"Memória Utilizada: {memoria:.2f} KB")
            else:
                messagebox.showinfo("Resultado", "Caminho não encontrado.")
        else:
            messagebox.showwarning("Entrada Inválida", "Por favor, forneça ambas as subestações de origem e destino.")

    def buscar_a_star(self):
        inicio = simpledialog.askstring("Busca A*", "Informe a subestação de origem:", parent=self.window)
        objetivo = simpledialog.askstring("Busca A*", "Informe a subestação de destino:", parent=self.window)
        if inicio and objetivo:
            caminho, custo, num_nos_visitados, tempo_execucao, memoria = self.rede.busca_a_star(inicio, objetivo)
            if caminho:
                messagebox.showinfo("Busca A*", f"Caminho: {' -> '.join(caminho)}, Custo: {custo}\n"
                                                f"Nós Visitados: {num_nos_visitados}\n"
                                                f"Tempo de Execução: {tempo_execucao:.4f} segundos\n"
                                                f"Memória Utilizada: {memoria:.2f} KB")
            else:
                messagebox.showinfo("Resultado", "Caminho não encontrado.")
        else:
            messagebox.showwarning("Entrada Inválida", "Por favor, forneça ambas as subestações de origem e destino.")

    def buscar_profundidade_iterativa(self):
        inicio = simpledialog.askstring("Busca Profundidade Iterativa", "Informe a subestação de origem:", parent=self.window)
        objetivo = simpledialog.askstring("Busca Profundidade Iterativa", "Informe a subestação de destino:", parent=self.window)
        if inicio and objetivo:
            caminho, num_nos_visitados, tempo_execucao, memoria = self.rede.profundidade_iterativa(inicio, objetivo)
            if caminho:
                messagebox.showinfo("Busca Profundidade Iterativa", f"Caminho: {' -> '.join(map(str, caminho))}\n"
                                                                    f"Nós Visitados: {num_nos_visitados}\n"
                                                                    f"Tempo de Execução: {tempo_execucao:.4f} segundos\n"
                                                                    f"Memória Utilizada: {memoria:.2f} KB")
            else:
                messagebox.showinfo("Resultado", "Caminho não encontrado.")
        else:
            messagebox.showwarning("Entrada Inválida", "Por favor, forneça ambas as subestações de origem e destino.")

    def visualizar_mapa(self):
        pos = nx.spring_layout(self.rede.grafo)
        labels = {n: f"{n}\nCarga Ideal: {self.rede.grafo.nodes[n]['carga_ideal']}\nCarga Atual: {self.rede.grafo.nodes[n]['carga_atual']}" for n in self.rede.grafo.nodes()}
        edge_labels = {(u, v): f"{dados['distancia']}km\n{dados['carga']}MW" for u, v, dados in self.rede.grafo.edges(data=True)}
        
        plt.figure(figsize=(10, 8))
        nx.draw(self.rede.grafo, pos, with_labels=True, labels=labels, node_size=2000, node_color="skyblue", font_size=8, font_weight="bold")
        nx.draw_networkx_edge_labels(self.rede.grafo, pos, edge_labels=edge_labels)
        plt.title("Mapa das Subestações e Conexões")
        plt.show()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    rede = RedeSubestacoes()
    app = InterfaceGrafica(rede)
    app.adicionar_subestacoes_e_conexoes() # Chama o método para adicionar subestações e conexões
    app.run()
