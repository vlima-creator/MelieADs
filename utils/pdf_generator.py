from fpdf import FPDF # fpdf2
from datetime import datetime
import pandas as pd

class PDFReportGenerator(FPDF):
    def __init__(self, analyzer, cliente_data, cat_foco, sub_foco, row_foco, chart_images=None):
        super().__init__()
        self.analyzer = analyzer
        self.cliente_data = cliente_data
        self.cat_foco = cat_foco
        self.sub_foco = sub_foco
        self.row_foco = row_foco
        self.chart_images = chart_images if chart_images else {}
        self.set_auto_page_break(auto=True, margin=20)
        
        # Cores da Identidade Visual (Moderno/Minimalista)
        self.primary_color = (30, 58, 138)    # Azul Noite (#1E3A8A)
        self.secondary_color = (243, 244, 246) # Cinza muito claro para fundos
        self.accent_color = (30, 58, 138)     # Azul Noite para destaques
        self.text_color = (31, 41, 55)        # Cinza escuro para texto
        self.light_text = (107, 114, 128)     # Cinza médio para detalhes
        
        self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])

    def header(self):
        # Barra superior decorativa
        self.set_fill_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.rect(0, 0, 210, 15, 'F')
        
        if self.page_no() == 1:
            self.set_y(20)
            self.set_font("Helvetica", "B", 22)
            self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
            self.cell(0, 15, "Relatório de Inteligência de Mercado", 0, 1, "L")
            
            self.set_font("Helvetica", "", 10)
            self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
            data_str = datetime.now().strftime("%d/%m/%Y")
            self.cell(0, 5, f"Gerado em: {data_str} | Análise Estratégica Exclusiva", 0, 1, "L")
            
            # Linha sutil de separação
            self.set_draw_color(229, 231, 235)
            self.line(10, 42, 200, 42)
            self.ln(15)
        else:
            self.set_y(20)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
            self.cell(0, 10, "Relatório Executivo - Inteligência de Mercado", 0, 0, "R")
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, "C")

    def section_title(self, title):
        self.ln(5)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.cell(0, 10, self.clean_text(title.upper()), 0, 1, "L")
        # Linha de destaque abaixo do título
        self.set_draw_color(self.accent_color[0], self.accent_color[1], self.accent_color[2])
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 20, self.get_y())
        self.ln(5)
        self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])

    def draw_card(self, title, value, x, y, w, h, color=None):
        if not color: color = self.secondary_color
        self.set_fill_color(color[0], color[1], color[2])
        self.rect(x, y, w, h, 'F')
        
        self.set_xy(x + 2, y + 2)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
        self.cell(w-4, 5, self.clean_text(title), 0, 1, "L")
        
        self.set_x(x + 2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.cell(w-4, 7, self.clean_text(value), 0, 1, "L")

    def add_summary(self):
        self.section_title("1. Visão Geral")
        empresa = self.cliente_data.get("empresa", "Empresa")
        categoria = self.cat_foco if self.cat_foco else "N/A"
        subcategoria = self.sub_foco if self.sub_foco else "N/A"
        
        # Texto introdutório
        self.set_font("Helvetica", "", 11)
        intro = f"Análise estratégica detalhada para {empresa}, focada no segmento de {subcategoria} ({categoria}). Este documento sintetiza oportunidades, projeções e ações recomendadas com base em dados reais de mercado."
        self.multi_cell(0, 6, self.clean_text(intro))
        self.ln(5)
        
        # Cards de KPI
        curr_y = self.get_y()
        
        # Garantir valores numéricos para os cálculos
        ticket_medio = float(self.cliente_data.get('ticket_medio', 0))
        margem = float(self.cliente_data.get('margem', 0))
        
        tm = f"R$ {self.format_br(ticket_medio)}"
        mg = f"{margem*100:.1f}%"
        
        tendencia_res = self.analyzer.calcular_tendencia(self.cat_foco)
        cresc_val = float(tendencia_res.get('crescimento_mensal', 0))
        cresc = f"{cresc_val:+.1f}% /mês"
        
        conf = self.analyzer.calcular_confianca(self.cat_foco, self.sub_foco)
        conf_val = f"{conf['score']}% ({conf['nivel']})"

        self.draw_card("TICKET MÉDIO ATUAL", tm, 10, curr_y, 45, 18)
        self.draw_card("MARGEM ATUAL", mg, 58, curr_y, 45, 18)
        self.draw_card("TENDÊNCIA MERCADO", cresc, 106, curr_y, 45, 18)
        self.draw_card("CONFIANÇA PROJEÇÃO", conf_val, 154, curr_y, 45, 18)
        
        self.set_y(curr_y + 25)

    def add_market_share_indicators(self):
        self.section_title("2. Indicadores de Market Share")
        
        curr_y = self.get_y()
        
        # 2.1. Score de Oportunidade (Design Premium)
        score = float(self.row_foco.get('Score', 0))
        status = self.row_foco.get('Status', 'N/A')
        
        # Background do Card do Score
        self.set_fill_color(250, 250, 250)
        self.rect(10, curr_y, 90, 55, 'F')
        self.set_draw_color(230, 230, 230)
        self.rect(10, curr_y, 90, 55, 'D')
        
        self.set_xy(10, curr_y + 5)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
        self.cell(90, 8, "SCORE DE OPORTUNIDADE", 0, 1, "C")
        
        # Grande número do Score
        self.set_font("Helvetica", "B", 32)
        self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.cell(90, 15, f"{score:.2f}", 0, 1, "C")
        
        # Barra de Progresso Colorida (Gauge Simulado)
        bar_x, bar_y, bar_w, bar_h = 20, curr_y + 32, 70, 4
        self.set_fill_color(230, 230, 230)
        self.rect(bar_x, bar_y, bar_w, bar_h, 'F') # Fundo da barra
        
        # Cor baseada no status
        if status == "FOCO": color = (30, 58, 138) # Azul Noite
        elif status == "OK": color = (59, 130, 246) # Azul Claro
        else: color = (156, 163, 175) # Cinza
        
        self.set_fill_color(color[0], color[1], color[2])
        fill_w = (score / 10.0) * bar_w
        self.rect(bar_x, bar_y, fill_w, bar_h, 'F') # Preenchimento
        
        self.set_xy(10, curr_y + 42)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(color[0], color[1], color[2])
        self.cell(90, 8, f"STATUS: {status}", 0, 1, "C")
        
        # 2.2. Comparação de Tickets (Design Premium)
        tk_cliente = float(self.row_foco.get('Ticket Cliente', 0))
        tk_mercado = float(self.row_foco.get('Ticket Mercado', 0))
        diff = ((tk_cliente / tk_mercado) - 1) * 100 if tk_mercado > 0 else 0
        
        # Background do Card do Ticket
        self.set_fill_color(250, 250, 250)
        self.rect(110, curr_y, 90, 55, 'F')
        self.set_draw_color(230, 230, 230)
        self.rect(110, curr_y, 90, 55, 'D')
        
        self.set_xy(110, curr_y + 5)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
        self.cell(90, 8, "COMPARAÇÃO DE TICKETS", 0, 1, "C")
        
        # Comparativo Visual (Infográfico)
        self.set_xy(115, curr_y + 15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])
        self.cell(40, 8, "Seu Ticket:", 0, 0, "L")
        self.set_font("Helvetica", "B", 10)
        self.cell(40, 8, f"R$ {self.format_br(tk_cliente)}", 0, 1, "R")
        
        self.set_x(115)
        self.set_font("Helvetica", "", 9)
        self.cell(40, 8, "Ticket Mercado:", 0, 0, "L")
        self.set_font("Helvetica", "B", 10)
        self.cell(40, 8, f"R$ {self.format_br(tk_mercado)}", 0, 1, "R")
        
        # Linha de Separação
        self.line(120, curr_y + 32, 190, curr_y + 32)
        
        self.set_xy(110, curr_y + 35)
        self.set_font("Helvetica", "B", 12)
        diff_color = (220, 38, 38) if abs(diff) > 20 else (5, 150, 105)
        self.set_text_color(diff_color[0], diff_color[1], diff_color[2])
        self.cell(90, 10, f"{diff:+.1f}% vs Mercado", 0, 1, "C")
        
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
        posicao = "Acima" if diff > 0 else "Abaixo"
        self.cell(90, 5, f"Sua precificação está {posicao} da média", 0, 1, "C")
            
        self.set_y(curr_y + 60)
        self.ln(5)

    def add_market_opportunities(self):
        self.section_title("3. Matriz de Oportunidades")
        df_ranking = self.analyzer.gerar_ranking()
        if df_ranking.empty: return

        # 2.1. Melhores Oportunidades
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.cell(0, 8, "2.1. Melhores Oportunidades (Foco e OK)", 0, 1, "L")
        self.ln(2)

        df_foco_ok = df_ranking[df_ranking["Status"].isin(["FOCO", "OK"])].sort_values(by="Score", ascending=False).head(5)
        
        if not df_foco_ok.empty:
            # Cabeçalho da Tabela
            self.set_fill_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 9)
            self.cell(80, 8, " SUBCATEGORIA", 0, 0, 'L', True)
            self.cell(40, 8, " MERCADO (6M)", 0, 0, 'C', True)
            self.cell(30, 8, " SCORE", 0, 0, 'C', True)
            self.cell(40, 8, " STATUS", 0, 1, 'C', True)
            
            self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])
            self.set_font("Helvetica", "", 8)
            fill = False
            for _, row in df_foco_ok.iterrows():
                self.set_fill_color(self.secondary_color[0], self.secondary_color[1], self.secondary_color[2])
                self.cell(80, 7, f" {self.clean_text(str(row['Subcategoria'])[:40])}", 0, 0, 'L', fill)
                self.cell(40, 7, f"R$ {self.format_br(row['Mercado (R$)'])}", 0, 0, 'C', fill)
                self.cell(30, 7, f"{row['Score']:.2f}", 0, 0, 'C', fill)
                status = row['Status']
                if status == "FOCO": self.set_text_color(220, 38, 38)
                elif status == "OK": self.set_text_color(5, 150, 105)
                self.cell(40, 7, status, 0, 1, 'C', fill)
                self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])
                fill = not fill
        else:
            self.set_font("Helvetica", "I", 9)
            self.cell(0, 8, "Nenhuma oportunidade de alto impacto identificada.", 0, 1)

        self.ln(5)

        # 2.2. Categorias a Monitorar/Evitar
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.cell(0, 8, "2.2. Categorias a Monitorar/Evitar", 0, 1, "L")
        self.ln(2)

        df_evitar = df_ranking[df_ranking["Status"] == "EVITAR"].sort_values(by="Score", ascending=True).head(5)
        
        if not df_evitar.empty:
            # Cabeçalho da Tabela
            self.set_fill_color(107, 114, 128) # Cinza para evitar
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 9)
            self.cell(80, 8, " SUBCATEGORIA", 0, 0, 'L', True)
            self.cell(40, 8, " MERCADO (6M)", 0, 0, 'C', True)
            self.cell(30, 8, " SCORE", 0, 0, 'C', True)
            self.cell(40, 8, " STATUS", 0, 1, 'C', True)
            
            self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])
            self.set_font("Helvetica", "", 8)
            fill = False
            for _, row in df_evitar.iterrows():
                self.set_fill_color(self.secondary_color[0], self.secondary_color[1], self.secondary_color[2])
                self.cell(80, 7, f" {self.clean_text(str(row['Subcategoria'])[:40])}", 0, 0, 'L', fill)
                self.cell(40, 7, f"R$ {self.format_br(row['Mercado (R$)'])}", 0, 0, 'C', fill)
                self.cell(30, 7, f"{row['Score']:.2f}", 0, 0, 'C', fill)
                self.set_text_color(156, 163, 175) # Cinza claro para status evitar
                self.cell(40, 7, row['Status'], 0, 1, 'C', fill)
                self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])
                fill = not fill
        else:
            self.set_font("Helvetica", "I", 9)
            self.cell(0, 8, "Nenhuma categoria crítica identificada no momento.", 0, 1)
        
        self.ln(5)

    def add_growth_scenarios(self):
        self.section_title("4. Cenários de Crescimento")
        res = self.analyzer.simular_cenarios(self.cat_foco, self.sub_foco)
        df = res.get("cenarios", pd.DataFrame())
        if df.empty: return

        # Tabela de Cenários
        self.set_fill_color(55, 65, 81)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        
        self.cell(40, 10, " CENÁRIO", 0, 0, 'L', True)
        self.cell(50, 10, " RECEITA PROJETADA", 0, 0, 'C', True)
        self.cell(50, 10, " LUCRO ESTIMADO", 0, 0, 'C', True)
        self.cell(50, 10, " CRESCIMENTO", 0, 1, 'C', True)
        
        self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])
        self.set_font("Helvetica", "", 9)
        
        fill = False
        for _, row in df.iterrows():
            self.set_fill_color(self.secondary_color[0], self.secondary_color[1], self.secondary_color[2])
            self.cell(40, 8, f" {self.clean_text(row['Cenário'])}", 0, 0, 'L', fill)
            self.cell(50, 8, f"R$ {self.format_br(row['Receita Projetada 6M'])}", 0, 0, 'C', fill)
            self.cell(50, 8, f"R$ {self.format_br(row['Lucro Projetado 6M'])}", 0, 0, 'C', fill)
            
            cresc = row['Crescimento (%)']
            if cresc > 0: self.set_text_color(5, 150, 105)
            else: self.set_text_color(220, 38, 38)
            
            self.cell(50, 8, f"{cresc:+.1f}%", 0, 1, 'C', fill)
            self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])
            fill = not fill
            
        # Box de Insight
        self.ln(4)
        self.set_fill_color(239, 246, 255)
        self.set_draw_color(self.accent_color[0], self.accent_color[1], self.accent_color[2])
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, "  INSIGHT ESTRATÉGICO", "L", 1, "L", True)
        self.set_font("Helvetica", "", 9)
        
        # Lógica de insight simplificada para o visual
        ticket_c = self.cliente_data.get('ticket_medio', 0)
        ticket_m = res.get('ticket_mercado', 0)
        if ticket_c < ticket_m * 0.9:
            msg = "Seu ticket está abaixo da média. Há oportunidade de aumento de margem sem perda de competitividade."
        elif ticket_c > ticket_m * 1.1:
            msg = "Seu ticket está acima da média. Foque em reforçar os diferenciais de valor para justificar o prêmio de preço."
        else:
            msg = "Preço equilibrado com o mercado. O foco deve ser em escala e eficiência operacional."
            
        self.multi_cell(0, 6, self.clean_text(f"  {msg}"), "L", "L", True)
        self.ln(5)

    def add_demand_projection(self):
        self.section_title("5. Projeção de Demanda (90 dias)")
        tendencia_res = self.analyzer.calcular_tendencia(self.cat_foco)
        valores_raw = tendencia_res.get("mensal", [0, 0, 0])
        # Garantir que todos os valores sejam float
        valores = [float(v) for v in valores_raw]
        
        self.set_font("Helvetica", "", 10)
        cresc_mensal = float(tendencia_res.get('crescimento_mensal', 0))
        self.cell(0, 8, self.clean_text(f"Tendência identificada: {tendencia_res['tendencia']} ({cresc_mensal:+.1f}% ao mês)"), 0, 1)
        
        # Mini gráfico/tabela de barras horizontal
        max_val = max(valores) if valores and max(valores) > 0 else 1
        meses = ["Mês 1", "Mês 2", "Mês 3"]
        
        for i, val in enumerate(valores):
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(self.light_text[0], self.light_text[1], self.light_text[2])
            self.cell(20, 8, meses[i], 0, 0)
            
            # Barra
            width = (val / max_val) * 120
            self.set_fill_color(self.accent_color[0], self.accent_color[1], self.accent_color[2])
            self.rect(35, self.get_y() + 2, width, 4, 'F')
            
            self.set_x(160)
            self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
            self.cell(30, 8, f"R$ {self.format_br(val)}", 0, 1, "R")
        
        self.ln(5)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.cell(0, 10, f"TOTAL PROJETADO: R$ {self.format_br(tendencia_res['projecao_3m'])}", 0, 1, "R")
        self.set_text_color(self.text_color[0], self.text_color[1], self.text_color[2])

    def add_anomalies_and_recommendations(self):
        self.section_title("6. Diagnóstico de Anomalias e Ação Imediata")
        
        # 5.1. Anomalias Detectadas
        anomalias = self.analyzer.identificar_anomalias(self.cat_foco)
        if anomalias:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(220, 38, 38) # Vermelho para anomalias
            self.cell(0, 8, "ALERTA: Anomalias Críticas Identificadas", 0, 1, "L")
            self.ln(2)
            
            for anom in anomalias:
                self.set_fill_color(254, 242, 242)
                self.set_font("Helvetica", "B", 9)
                self.set_text_color(31, 41, 55)
                msg = f"[{anom['tipo']}] {anom['subcategoria']}: {anom['mensagem']}"
                self.multi_cell(0, 7, self.clean_text(msg), 0, "L", True)
                self.ln(2)
        else:
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(5, 150, 105)
            self.cell(0, 8, "Nenhuma anomalia crítica detectada no portfólio atual.", 0, 1, "L")
        
        self.ln(5)
        
        # 5.2. Matriz de Recomendação Automática
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
        self.cell(0, 8, "5.2. Matriz de Recomendação Automática (Ação Imediata)", 0, 1, "L")
        self.ln(2)
        
        lista_plano = self.analyzer.gerar_plano_acao(self.cat_foco)
        plano_foco = next((p for p in lista_plano if p["Subcategoria"] == self.sub_foco), None)
        
        if plano_foco:
            # Recomendação Curta e Ação Imediata em Destaque
            self.set_fill_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
            self.set_text_color(255, 255, 255)
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 10, self.clean_text(f"  ESTRATÉGIA: {plano_foco.get('Recomendacao_Curta', 'N/A')}"), 0, 1, "L", True)
            
            self.set_fill_color(243, 244, 246)
            self.set_text_color(31, 41, 55)
            self.set_font("Helvetica", "B", 10)
            self.cell(0, 8, "  AÇÃO IMEDIATA RECOMENDADA:", 0, 1, "L", True)
            self.set_font("Helvetica", "", 10)
            self.multi_cell(0, 7, self.clean_text(f"  {plano_foco.get('Acao_Imediata', 'N/A')}"), 0, "L", True)
            self.ln(5)

            # Detalhamento das Ações
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(self.primary_color[0], self.primary_color[1], self.primary_color[2])
            self.cell(0, 8, "Detalhamento da Análise:", 0, 1, "L")
            
            self.set_font("Helvetica", "", 10)
            self.set_text_color(31, 41, 55)
            for acao in plano_foco.get("Ações", []):
                acao_limpa = acao.replace("**", "")
                self.set_x(15)
                self.multi_cell(0, 6, self.clean_text(f"- {acao_limpa}"))
                self.ln(1)
        else:
            self.set_font("Helvetica", "I", 10)
            self.cell(0, 8, "Análise detalhada não disponível para esta subcategoria.", 0, 1, "L")

    def clean_text(self, text):
        if not text: return ""
        replacements = {
            '✅': '[OK]', '🚀': '[GO]', '⚠️': '[!]', '💡': '[i]', '💰': '[$]', '🎯': '[TARGET]', 
            '•': '-', '·': '-', '—': '-', '–': '-', '“': '"', '”': '"', '‘': "'", '’': "'",
            '📈': '[UP]', '📉': '[DOWN]', '📦': '[MIX]', '🛒': '[VENDAS]', '🛠️': '[ACAO]'
        }
        for char, rep in replacements.items():
            text = text.replace(char, rep)
        try:
            return text.encode('latin-1', 'replace').decode('latin-1').replace('?', ' ')
        except:
            return "".join([c if ord(c) < 256 else ' ' for c in text])

    def format_br(self, value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:,.1f}M".replace(".", "X").replace(",", ".").replace("X", ",")
        elif value >= 1_000:
            return f"{value / 1_000:,.1f}K".replace(".", "X").replace(",", ".").replace("X", ",")
        else:
            return f"{value:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")

    def generate_report(self, filename="relatorio_executivo.pdf"):
        self.add_page()
        self.alias_nb_pages()
        self.add_summary()
        self.add_market_opportunities()
        self.add_growth_scenarios()
        self.add_demand_projection()
        self.add_anomalies_and_recommendations()
        self.output(filename)

    def gerar_relatorio(self):
        """Gera o relatório em memória e retorna bytes para o Streamlit"""
        self.add_page()
        self.add_summary()
        self.add_market_share_indicators()
        self.add_market_opportunities()
        self.add_growth_scenarios()
        self.add_demand_projection()
        self.add_anomalies_and_recommendations()
        
        # No fpdf2, output() sem argumentos retorna um bytearray
        # Convertemos para bytes para evitar o erro "Invalid binary data format"
        pdf_data = self.output()
        return bytes(pdf_data) if isinstance(pdf_data, (bytearray, list)) else pdf_data
