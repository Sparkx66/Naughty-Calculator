
import ast
import json
import math
import operator
from pathlib import Path
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle


Window.size = (360, 640)
Window.clearcolor = (0.04, 0.06, 0.14, 1)

AZUL_FUNDO = (0.04, 0.06, 0.14, 1)
AZUL_PAINEL = (0.07, 0.10, 0.21, 1)
AZUL_BOTAO = (0.10, 0.14, 0.27, 1)
AZUL_OPERADOR = (0.30, 0.22, 0.75, 1)
AZUL_IGUAL = (0.20, 0.42, 1.00, 1)
AZUL_ESPECIAL = (0.12, 0.24, 0.42, 1)
BRANCO = (0.94, 0.97, 1, 1)


class BotaoTecnologico(Button):
    def __init__(self, cor_fundo=AZUL_BOTAO, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = BRANCO
        self.bold = True

        self.cor_fundo = cor_fundo

        with self.canvas.before:
            self.cor = Color(*self.cor_fundo)
            self.forma = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)]
            )

        self.bind(pos=self.atualizar_forma, size=self.atualizar_forma)

    def atualizar_forma(self, *args):
        self.forma.pos = self.pos
        self.forma.size = self.size


class CalculadoraApp(App):
    title="Naughty Calculator"

    def build(self):
        self.expressao = ""
        self.resultado_mostrado = False
        self.aguardando_porcentagem = False
        self.base_porcentagem = ""

        self.historico = []
        self.arquivo_historico = (
            Path(__file__).resolve().parent / "historico.json"
        )

        self.carregar_historico()

        principal = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        with principal.canvas.before:
            Color(*AZUL_FUNDO)
            self.fundo_principal = RoundedRectangle(
                pos=principal.pos,
                size=principal.size
            )

        principal.bind(
            pos=self.atualizar_fundo,
            size=self.atualizar_fundo
        )

        titulo = Label(
            text="[b]Naughty Calculator[/b]",
            markup=True,
            font_size="16sp",
            color=(0.48, 0.65, 1, 1),
            size_hint=(1, 0.07)
        )
        principal.add_widget(titulo)

        painel_visor = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            size_hint=(1, 0.17)
        )

        with painel_visor.canvas.before:
            Color(*AZUL_PAINEL)
            painel_visor.fundo = RoundedRectangle(
                pos=painel_visor.pos,
                size=painel_visor.size,
                radius=[dp(16)]
            )

        painel_visor.bind(
            pos=lambda obj, valor: self.atualizar_painel(obj),
            size=lambda obj, valor: self.atualizar_painel(obj)
        )

        self.visor = Label(
            text="0",
            font_size="32sp",
            color=BRANCO,
            halign="right",
            valign="middle",
            size_hint=(1, 1)
        )
        self.visor.bind(size=self.ajustar_visor)
        painel_visor.add_widget(self.visor)

        principal.add_widget(painel_visor)

        botoes = [
            ["C", "⌫", "√", "%"],
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["//", "0", ".", "+"],
            ["**", "(", ")", "="]
        ]

        grade = GridLayout(
            cols=4,
            spacing=dp(8),
            size_hint=(1, 0.65)
        )

        for linha in botoes:
            for texto in linha:
                if texto == "=":
                    cor = AZUL_IGUAL
                elif texto in ("+", "-", "*", "/", "//", "**"):
                    cor = AZUL_OPERADOR
                elif texto in ("C", "⌫", "√", "%", "(", ")"):
                    cor = AZUL_ESPECIAL
                else:
                    cor = AZUL_BOTAO

                botao = BotaoTecnologico(
                    text=texto,
                    cor_fundo=cor,
                    font_size="21sp"
                )
                botao.bind(on_release=self.ao_clicar)
                grade.add_widget(botao)

        principal.add_widget(grade)

        rodape = BoxLayout(
            orientation="horizontal",
            size_hint=(1, 0.10),
            spacing=dp(8)
        )

        botao_historico = BotaoTecnologico(
            text="Histórico",
            cor_fundo=AZUL_ESPECIAL,
            font_size="14sp"
        )
        botao_historico.bind(
            on_release=lambda *_: self.mostrar_historico()
        )
        rodape.add_widget(botao_historico)

        botao_limpar = BotaoTecnologico(
            text="Limpar histórico",
            cor_fundo=AZUL_ESPECIAL,
            font_size="14sp"
        )
        botao_limpar.bind(
            on_release=lambda *_: self.confirmar_limpar_historico()
        )
        rodape.add_widget(botao_limpar)

        principal.add_widget(rodape)

        return principal

    def atualizar_fundo(self, instancia, *args):
        self.fundo_principal.pos = instancia.pos
        self.fundo_principal.size = instancia.size

    def atualizar_painel(self, instancia, *args):
        instancia.fundo.pos = instancia.pos
        instancia.fundo.size = instancia.size

    def ajustar_visor(self, instancia, tamanho):
        instancia.text_size = tamanho

    def carregar_historico(self):
        try:
            if self.arquivo_historico.exists():
                with self.arquivo_historico.open(
                    "r",
                    encoding="utf-8"
                ) as arquivo:
                    dados = json.load(arquivo)

                self.historico = (
                    dados if isinstance(dados, list) else []
                )
            else:
                self.historico = []
                self.salvar_historico()

        except (OSError, json.JSONDecodeError):
            self.historico = []

    def salvar_historico(self):
        try:
            with self.arquivo_historico.open(
                "w",
                encoding="utf-8"
            ) as arquivo:
                json.dump(
                    self.historico,
                    arquivo,
                    ensure_ascii=False,
                    indent=4
                )
            return True

        except OSError:
            self.mostrar_mensagem(
                "Erro",
                "Não foi possível salvar o histórico."
            )
            return False

    def registrar_historico(self, operacao, resultado):
        registro = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "operacao": operacao,
            "resultado": str(resultado)
        }

        self.historico.append(registro)
        self.salvar_historico()

    def mostrar_mensagem(self, titulo, mensagem):
        conteudo = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10)
        )

        texto = Label(
            text=mensagem,
            halign="center",
            valign="middle"
        )
        texto.bind(
            size=lambda instancia, tamanho:
            setattr(instancia, "text_size", tamanho)
        )
        conteudo.add_widget(texto)

        botao = BotaoTecnologico(
            text="OK",
            cor_fundo=AZUL_IGUAL,
            size_hint=(1, None),
            height=dp(45)
        )
        conteudo.add_widget(botao)

        popup = Popup(
            title=titulo,
            content=conteudo,
            size_hint=(0.85, 0.4)
        )

        botao.bind(on_release=popup.dismiss)
        popup.open()

    def mostrar_historico(self):
        conteudo = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        rolagem = ScrollView()

        lista = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )
        lista.bind(minimum_height=lista.setter("height"))

        if not self.historico:
            lista.add_widget(
                Label(
                    text="Nenhum cálculo registrado.",
                    size_hint_y=None,
                    height=dp(50)
                )
            )
        else:
            for registro in reversed(self.historico):
                texto = (
                    f"{registro.get('data', '')}\n"
                    f"{registro.get('operacao', '')}\n"
                    f"Resultado: {registro.get('resultado', '')}"
                )

                item = Label(
                    text=texto,
                    color=BRANCO,
                    size_hint_y=None,
                    height=dp(85),
                    halign="left",
                    valign="middle"
                )
                item.bind(
                    size=lambda instancia, tamanho:
                    setattr(instancia, "text_size", tamanho)
                )
                lista.add_widget(item)

        rolagem.add_widget(lista)
        conteudo.add_widget(rolagem)

        botao_fechar = BotaoTecnologico(
            text="Fechar",
            cor_fundo=AZUL_IGUAL,
            size_hint=(1, None),
            height=dp(45)
        )
        conteudo.add_widget(botao_fechar)

        popup = Popup(
            title="Histórico de cálculos",
            content=conteudo,
            size_hint=(0.9, 0.8),
            separator_color=AZUL_IGUAL,
            background_color=AZUL_PAINEL
        )

        botao_fechar.bind(on_release=popup.dismiss)
        popup.open()

    def confirmar_limpar_historico(self):
        conteudo = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(10)
        )

        conteudo.add_widget(
            Label(text="Deseja apagar todo o histórico?")
        )

        botoes = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint=(1, None),
            height=dp(45)
        )

        botao_sim = BotaoTecnologico(
            text="Sim",
            cor_fundo=AZUL_IGUAL
        )
        botao_nao = BotaoTecnologico(
            text="Não",
            cor_fundo=AZUL_ESPECIAL
        )

        botoes.add_widget(botao_sim)
        botoes.add_widget(botao_nao)
        conteudo.add_widget(botoes)

        popup = Popup(
            title="Limpar histórico",
            content=conteudo,
            size_hint=(0.85, 0.35),
            auto_dismiss=False,
            background_color=AZUL_PAINEL
        )

        botao_sim.bind(
            on_release=lambda *_: self.limpar_historico(popup)
        )
        botao_nao.bind(on_release=popup.dismiss)

        popup.open()

    def limpar_historico(self, popup):
        self.historico = []

        if self.salvar_historico():
            popup.dismiss()
            self.mostrar_mensagem(
                "Histórico",
                "Histórico apagado com sucesso."
            )

    def calcular_expressao(self, expressao):
        operadores = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Pow: operator.pow
        }

        def avaliar(no):
            if isinstance(no, ast.Expression):
                return avaliar(no.body)

            if isinstance(no, ast.Constant):
                if type(no.value) in (int, float):
                    return no.value
                raise ValueError("Valor inválido.")

            if isinstance(no, ast.BinOp):
                tipo = type(no.op)

                if tipo not in operadores:
                    raise ValueError("Operação não permitida.")

                esquerda = avaliar(no.left)
                direita = avaliar(no.right)

                if tipo is ast.Pow and abs(direita) > 100:
                    raise ValueError("Expoente muito grande.")

                return operadores[tipo](esquerda, direita)

            if isinstance(no, ast.UnaryOp):
                valor = avaliar(no.operand)

                if isinstance(no.op, ast.UAdd):
                    return valor

                if isinstance(no.op, ast.USub):
                    return -valor

                raise ValueError("Operação não permitida.")

            raise ValueError("Expressão inválida.")

        arvore = ast.parse(expressao, mode="eval")
        resultado = avaliar(arvore)

        if isinstance(resultado, complex):
            raise ValueError("Resultado complexo não suportado.")

        if not math.isfinite(resultado):
            raise ValueError("Resultado fora do limite.")

        return resultado

    def formatar_resultado(self, resultado):
        if isinstance(resultado, float) and resultado.is_integer():
            return str(int(resultado))

        return str(round(resultado, 10))

    def ao_clicar(self, botao):
        texto = botao.text

        if texto == "C":
            self.limpar()
            return

        if texto == "⌫":
            self.apagar_ultimo()
            return

        if texto == "√":
            self.calcular_raiz()
            return

        if texto == "%":
            self.iniciar_porcentagem()
            return

        if texto == "=":
            self.calcular()
            return

        operadores = ("+", "-", "*", "/", "//", "**")

        if self.aguardando_porcentagem:
            if texto in operadores or texto in ("(", ")"):
                return

            if self.resultado_mostrado:
                self.expressao = ""

            self.expressao += texto
            self.resultado_mostrado = False
            self.visor.text = self.expressao or "0"
            return

        if self.resultado_mostrado:
            if texto not in operadores:
                self.expressao = ""

            self.resultado_mostrado = False

        self.expressao += texto
        self.visor.text = self.expressao or "0"

    def limpar(self):
        self.expressao = ""
        self.resultado_mostrado = False
        self.aguardando_porcentagem = False
        self.base_porcentagem = ""
        self.visor.text = "0"

    def apagar_ultimo(self):
        if self.aguardando_porcentagem:
            self.expressao = self.expressao[:-1]
            self.visor.text = self.expressao or (
                f"{self.base_porcentagem}%"
            )
            return

        self.expressao = self.expressao[:-1]
        self.resultado_mostrado = False
        self.visor.text = self.expressao or "0"

    def iniciar_porcentagem(self):
        if not self.expressao:
            return

        self.base_porcentagem = self.expressao
        self.expressao = ""
        self.aguardando_porcentagem = True
        self.resultado_mostrado = False
        self.visor.text = f"{self.base_porcentagem}%"

    def calcular(self):
        if self.aguardando_porcentagem:
            try:
                base = self.calcular_expressao(
                    self.base_porcentagem
                )
                porcentagem = self.calcular_expressao(
                    self.expressao
                )

                resultado = base * porcentagem / 100
                operacao = (
                    f"{self.base_porcentagem}% de "
                    f"{self.expressao}"
                )

                resultado_formatado = self.formatar_resultado(
                    resultado
                )

                self.registrar_historico(
                    operacao,
                    resultado_formatado
                )

                self.expressao = resultado_formatado
                self.visor.text = resultado_formatado
                self.aguardando_porcentagem = False
                self.base_porcentagem = ""
                self.resultado_mostrado = True

            except (
                ValueError,
                SyntaxError,
                TypeError,
                ZeroDivisionError,
                OverflowError
            ) as erro:
                self.mostrar_mensagem("Erro", str(erro))
                self.limpar()

            return

        if not self.expressao:
            return

        try:
            operacao = self.expressao
            resultado = self.calcular_expressao(operacao)
            resultado_formatado = self.formatar_resultado(resultado)

            self.registrar_historico(
                operacao,
                resultado_formatado
            )

            self.expressao = resultado_formatado
            self.visor.text = resultado_formatado
            self.resultado_mostrado = True

        except (
            ValueError,
            SyntaxError,
            TypeError,
            ZeroDivisionError,
            OverflowError
        ) as erro:
            self.mostrar_mensagem("Erro no cálculo", str(erro))
            self.limpar()

    def calcular_raiz(self):
        if not self.expressao:
            return

        try:
            operacao = f"√({self.expressao})"
            valor = self.calcular_expressao(self.expressao)

            if valor < 0:
                raise ValueError(
                    "Não existe raiz real de número negativo."
                )

            resultado = math.sqrt(valor)
            resultado_formatado = self.formatar_resultado(resultado)

            self.registrar_historico(
                operacao,
                resultado_formatado
            )

            self.expressao = resultado_formatado
            self.visor.text = resultado_formatado
            self.resultado_mostrado = True

        except (
            ValueError,
            SyntaxError,
            TypeError,
            ZeroDivisionError,
            OverflowError
        ) as erro:
            self.mostrar_mensagem(
                "Erro na raiz quadrada",
                str(erro)
            )
            self.limpar()


if __name__ == "__main__":
    CalculadoraApp().run()
