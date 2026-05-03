"""Gera PLANO_EXECUCAO.pdf na raiz do projeto.

Uso:
    .\.venv\Scripts\python.exe -X utf8 scripts\generate_plan_pdf.py
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "PLANO_EXECUCAO.pdf"

NAVY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c97a30")
SOFT = colors.HexColor("#f3f1ec")
GREY = colors.HexColor("#666666")


def build_styles():
    base = getSampleStyleSheet()

    styles = {
        "Title": ParagraphStyle(
            "TitleX", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=26, leading=32,
            textColor=NAVY, spaceAfter=6,
        ),
        "Subtitle": ParagraphStyle(
            "SubX", parent=base["Normal"],
            fontName="Helvetica", fontSize=12, leading=16,
            textColor=GREY, spaceAfter=18,
        ),
        "H1": ParagraphStyle(
            "H1X", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=18, leading=22,
            textColor=NAVY, spaceBefore=18, spaceAfter=10,
        ),
        "H2": ParagraphStyle(
            "H2X", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=14, leading=18,
            textColor=NAVY, spaceBefore=12, spaceAfter=6,
        ),
        "H3": ParagraphStyle(
            "H3X", parent=base["Heading3"],
            fontName="Helvetica-Bold", fontSize=11.5, leading=15,
            textColor=ACCENT, spaceBefore=8, spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "BodyX", parent=base["BodyText"],
            fontName="Helvetica", fontSize=10.5, leading=15,
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "Bullet": ParagraphStyle(
            "BulletX", parent=base["BodyText"],
            fontName="Helvetica", fontSize=10.5, leading=14,
            alignment=TA_LEFT, spaceAfter=2, leftIndent=0,
        ),
        "Code": ParagraphStyle(
            "CodeX", parent=base["Code"],
            fontName="Courier", fontSize=9, leading=12,
            backColor=SOFT, textColor=colors.HexColor("#222"),
            leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=8,
            borderPadding=6,
        ),
        "Caption": ParagraphStyle(
            "CaptionX", parent=base["Italic"],
            fontName="Helvetica-Oblique", fontSize=9, leading=12,
            textColor=GREY, spaceAfter=10,
        ),
    }
    return styles


def bullets(items, style):
    flowables = []
    for it in items:
        flowables.append(ListItem(Paragraph(it, style), leftIndent=14, value="bullet"))
    return ListFlowable(flowables, bulletType="bullet", start="•",
                        bulletColor=NAVY, leftIndent=14, bulletFontSize=10)


def info_table(rows):
    t = Table(rows, colWidths=[4.2 * cm, 12.0 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), SOFT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def phase_block(s, num, title, fields, items_by_section):
    """Bloco padrão de uma fase."""
    out = []
    out.append(Paragraph(f"Fase {num} — {title}", s["H2"]))
    out.append(info_table([
        ["Objetivo", fields["objetivo"]],
        ["Esforço estimado", fields["esforco"]],
        ["Pré-requisitos", fields["prereq"]],
        ["Critério de aceitação", fields["aceitacao"]],
    ]))
    out.append(Spacer(1, 6))
    for sec_title, items in items_by_section.items():
        out.append(Paragraph(sec_title, s["H3"]))
        if isinstance(items, str):
            out.append(Paragraph(items, s["Body"]))
        else:
            out.append(bullets(items, s["Bullet"]))
            out.append(Spacer(1, 2))
    return out


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.2 * cm, "analise_acoes — Plano de Execução")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"pág. {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#dddddd"))
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def build_story(s):
    story = []

    # ---------- Capa ----------
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("Plano de Execução", s["Title"]))
    story.append(Paragraph(
        "Projeto <b>analise_acoes</b> — Sistema de projeção do próximo pregão "
        "para PETR4, VALE3 e ITUB4 na B3.",
        s["Subtitle"],
    ))
    story.append(Spacer(1, 8 * cm))
    story.append(info_table([
        ["Repositório", "github.com/vanderbarbosa/analise_acoes"],
        ["Stack", "Python 3.11 · Flask 3 · SQLAlchemy 2 · SQLite · yfinance · feedparser · Plotly · APScheduler"],
        ["Tickers", "PETR4 · VALE3 · ITUB4 (B3, sufixo .SA)"],
        ["Documento gerado em", date.today().isoformat()],
        ["Autor", "Vanderlei Barbosa (com apoio do Claude Code)"],
    ]))
    story.append(PageBreak())

    # ---------- Sumário Executivo ----------
    story.append(Paragraph("1. Sumário executivo", s["H1"]))
    story.append(Paragraph(
        "O <b>analise_acoes</b> é um site Python de apoio à decisão para três ações da B3. "
        "Combina <b>indicadores técnicos</b> calculados sobre o histórico do yfinance com um "
        "<b>score de notícias</b> obtido por coleta RSS e classificação heurística, e gera "
        "uma <b>projeção direcional</b> (alta/baixa/neutro) com magnitude estimada por ATR para o próximo pregão.",
        s["Body"],
    ))
    story.append(Paragraph(
        "A arquitetura, o pipeline de dados e o site Flask já estão implementados e funcionando. "
        "Este documento descreve o plano para <b>concluir o produto</b> — fechando lacunas de testes, "
        "atualização de dados, automação, validação empírica (backtest) e melhorias de UX — em <b>seis fases</b> "
        "incrementais, organizadas por valor agregado e ordem de dependência. Cada fase é entregável de forma independente e o projeto pode parar entre fases sem deixar estado quebrado.",
        s["Body"],
    ))
    story.append(Paragraph(
        "Esforço total estimado: <b>~14 a 22 horas</b> de trabalho (excluindo Fase 6 opcional, +20 h se ativada).",
        s["Body"],
    ))
    story.append(Paragraph(
        "Disclaimer: o produto é <b>estudo / apoio à decisão</b>, não recomendação de investimento. "
        "O teto realista de acerto direcional intradiário/diário em um modelo heurístico desta natureza é estimado em 52–58%.",
        s["Caption"],
    ))

    # ---------- Visão do Produto ----------
    story.append(Paragraph("2. Visão do produto", s["H1"]))

    story.append(Paragraph("2.1 Propósito", s["H2"]))
    story.append(Paragraph(
        "Disponibilizar, em uma interface web simples, uma leitura diária consolidada para "
        "PETR4, VALE3 e ITUB4 que ajude a formar opinião sobre a tendência de curto prazo, "
        "evitando que o usuário precise consultar múltiplas fontes de cotação, indicadores e notícias.",
        s["Body"],
    ))

    story.append(Paragraph("2.2 Escopo", s["H2"]))
    story.append(bullets([
        "Acompanhamento contínuo dos 3 tickers acima (mais podem ser adicionados via <i>config.py</i>).",
        "Coleta diária de notícias via RSS (InfoMoney, Money Times, G1 Economia).",
        "Classificação heurística por categoria (macroeconômica, política, fundamentos, outro) e sentimento (positivo/negativo).",
        "Cálculo de indicadores técnicos: RSI(14), MACD(12,26,9), EMAs(9,21,50), Bandas de Bollinger(20,2σ), ATR(14).",
        "Projeção do próximo pregão: direção, magnitude estimada (% sobre ATR) e nível de confiança.",
        "Persistência completa em SQLite para auditoria e backtest.",
        "Site Flask com listagem de tickers, página de detalhe, gráfico interativo (Plotly) e lista de notícias recentes.",
    ], s["Bullet"]))

    story.append(Paragraph("2.3 Fora do escopo", s["H2"]))
    story.append(bullets([
        "Execução de ordens, integração com corretora ou qualquer ação automatizada de trading.",
        "Recomendação personalizada de carteira ou perfil de investidor.",
        "Análise intradia (timeframes &lt; 1 dia).",
        "Cobertura de ativos fora dos 3 tickers configurados (sem impedimento técnico, mas fora do MVP).",
        "Modelos pesados de NLP / Deep Learning na fase inicial — substituíveis na Fase 6 opcional.",
    ], s["Bullet"]))

    # ---------- Estado Atual ----------
    story.append(Paragraph("3. Estado atual (baseline)", s["H1"]))
    story.append(Paragraph(
        "Snapshot tirado em <b>" + date.today().isoformat() + "</b> a partir do banco "
        "<i>data/analise.db</i> e da árvore de código do repositório.",
        s["Caption"],
    ))

    story.append(Paragraph("3.1 Componentes implementados", s["H2"]))
    story.append(info_table([
        ["Camada de dados", "src/db/models.py — schema SQLAlchemy 2.0 com 5 tabelas: tickers, price_daily, news_raw, news_scored, predictions. init_db() idempotente, com seed automático dos tickers a partir de config.TICKERS."],
        ["Pipeline de notícias", "src/news/{collect,filter,classify,score}.py — coleta RSS, filtragem por regex+credibilidade, classificação heurística por palavras-chave, agregação ponderada em janela de 48 h."],
        ["Pipeline de preços", "src/prices/{fetch,indicators,signal}.py — download via yfinance, cálculo puro-pandas dos indicadores (sem pandas-ta) e heurística de tech_score em [-1, 1]."],
        ["Projetor", "src/prediction/projector.py — combina news e tech via WEIGHT_NEWS/WEIGHT_TECHNICAL, aplica zona morta de ±0,15 e estima magnitude pela ATR%."],
        ["Jobs", "src/jobs/{backfill,daily}.py — backfill histórico do Q1 2026 e job diário (notícias + preços + projeção)."],
        ["Flask app", "app.py — rotas / e /ticker/<symbol>, três filtros Jinja (brl, pct, d), gráfico Plotly server-rendered."],
        ["Templates / estilo", "templates/{base,index,ticker}.html, static/css/app.css (3,5 KB)."],
        ["DevOps local", ".claude/hooks/auto-commit.ps1 e .claude/settings.json — auto-commit + push após cada turno do Claude."],
    ]))

    story.append(Paragraph("3.2 Métricas atuais do banco", s["H2"]))
    story.append(info_table([
        ["Tickers cadastrados", "3 (PETR4, VALE3, ITUB4)"],
        ["Candles em price_daily", "183 (2026-01-02 a 2026-03-31)"],
        ["Notícias brutas (news_raw)", "6"],
        ["Notícias scoradas (news_scored)", "6"],
        ["Predictions geradas", "3 (uma por ticker)"],
        ["Tamanho do arquivo SQLite", "~127 KB"],
    ]))

    story.append(PageBreak())

    # ---------- Lacunas ----------
    story.append(Paragraph("4. Lacunas identificadas", s["H1"]))

    story.append(Paragraph("4.1 Críticas (bloqueiam encerramento do projeto)", s["H2"]))
    story.append(bullets([
        "<b>Defasagem de preços:</b> backfill termina em 2026-03-31 e a data atual é 2026-05-03 — ~5 semanas de candles ausentes; o site exibe dados desatualizados.",
        "<b>Suite de testes inexistente:</b> a pasta tests/ contém apenas __init__.py. Não há cobertura para indicadores, sinais técnicos, classificador, agregador de notícias ou projetor — riscos altos de regressão silenciosa.",
        "<b>Sem validação empírica:</b> não há backtest comparando predictions.for_date com o close real. Sem isso, a tese de “52–58 % de acerto” permanece não verificada.",
        "<b>Pipeline manual:</b> daily.py precisa ser executado à mão. Falta scheduler (APScheduler já está em requirements.txt mas não é usado).",
    ], s["Bullet"]))

    story.append(Paragraph("4.2 Importantes (qualidade do produto)", s["H2"]))
    story.append(bullets([
        "Logging estruturado ausente — usa apenas print(). Dificulta diagnóstico em execução automatizada.",
        "Tratamento de erros em yfinance: rede caída, ticker inválido ou rate-limit não geram retry/backoff.",
        "RSS pode duplicar artigos com URL canônica diferente (utm_source, fbclid). Deduplicação atual é por link estrito.",
        "Página de detalhe não mostra histórico do tech_score nem do news_score ao longo do tempo.",
        "Não há indicador visual de “última atualização do pipeline” no site, dificultando saber se o número exibido é fresco.",
    ], s["Bullet"]))

    story.append(Paragraph("4.3 Desejáveis (evolução pós-MVP)", s["H2"]))
    story.append(bullets([
        "Substituir o classificador heurístico por NLP real (zero-shot + sentimento PT-BR) — Fase 6 opcional.",
        "Adicionar modo as-of &lt;data&gt; para reprocessar uma data passada (útil para depuração).",
        "Permitir cadastro de novos tickers via UI (hoje só via config.py).",
        "Exportação CSV de predictions vs realizado.",
        "Alerta por e-mail quando a confiança ultrapassar um limiar.",
    ], s["Bullet"]))

    # ---------- Plano em fases ----------
    story.append(PageBreak())
    story.append(Paragraph("5. Plano em fases", s["H1"]))
    story.append(Paragraph(
        "Cada fase é um entregável fechado. As Fases 1 a 4 são suficientes para considerar o "
        "MVP concluído; a Fase 5 polariza melhor a percepção de qualidade; a Fase 6 é opcional "
        "e introduz dependência pesada (PyTorch).",
        s["Body"],
    ))

    # ---- Fase 1 ----
    story.extend(phase_block(s, 1, "Atualização de dados e estabilização do baseline", {
        "objetivo": "Eliminar a defasagem de preços, garantir que o pipeline diário roda end-to-end "
                    "sem erro, e deixar o site exibindo dados consistentes para o pregão mais recente.",
        "esforco": "1,5 a 2,5 h",
        "prereq": "Nenhum (ponto de partida)",
        "aceitacao": "Em data/analise.db existe price_daily até o último pregão útil; "
                     "executar `python -m src.jobs.daily` finaliza com 0 erros; "
                     "site mostra a data correta no card de cada ticker.",
    }, {
        "Escopo de trabalho": [
            "Atualizar BACKFILL_END em config.py para o último pregão útil disponível.",
            "Rodar src.jobs.backfill para preencher o gap (estratégia: ampliar janela; o DELETE+INSERT do backfill é idempotente).",
            "Executar src.jobs.daily uma vez para validar a integração ponta-a-ponta.",
            "Conferir visualmente as três páginas (/, /ticker/PETR4, /ticker/VALE3, /ticker/ITUB4).",
            "Capturar quaisquer erros encontrados (encoding, rate-limit, schema) e abrir tickets internos.",
        ],
        "Arquivos afetados": [
            "config.py (BACKFILL_END)",
            "Possivelmente src/prices/fetch.py (caso surja erro de schema do yfinance)",
            "data/analise.db (estado atualizado, não versionado)",
        ],
        "Riscos específicos": [
            "yfinance pode retornar DataFrame com MultiIndex inesperado em janelas grandes — já tratado em fetch.py mas vale revalidar.",
            "RSS retorna apenas notícias dos últimos dias; news_raw continuará com volume baixo até a Fase 4 entrar em operação contínua.",
        ],
    }))

    # ---- Fase 2 ----
    story.extend(phase_block(s, 2, "Suite de testes automatizados", {
        "objetivo": "Cobrir as funções puras do pipeline com testes determinísticos para "
                    "permitir refatorações futuras com segurança e detectar regressões cedo.",
        "esforco": "3 a 5 h",
        "prereq": "Fase 1 concluída (baseline estável)",
        "aceitacao": "`pytest` finaliza com ≥ 25 testes passando em &lt; 5 s, sem chamadas de "
                     "rede; cobertura mínima de 80 % em src/prices/indicators.py, src/prices/signal.py, "
                     "src/news/classify.py, src/news/score.py e src/prediction/projector.py.",
    }, {
        "Estratégia de teste": [
            "Testar apenas funções puras (sem yfinance/RSS/HTTP). Para módulos com I/O, isolar a parte determinística e testar separadamente.",
            "Usar fixtures pytest em conftest.py para criar DataFrames OHLCV sintéticos reproducíveis (seed fixa).",
            "Para a camada de DB, usar SQLite em :memory: via fixture session (não tocar data/analise.db).",
            "Sem mocks de bibliotecas externas no MVP — preferir testar camadas puras.",
        ],
        "Arquivos a criar": [
            "tests/conftest.py — fixtures (sample_ohlcv, in_memory_session, seeded_tickers).",
            "tests/test_indicators.py — RSI extremo, MACD cruzando zero, Bollinger com vol baixa/alta, ATR consistente com TR manual.",
            "tests/test_signal.py — entradas com NaN, RSI sobrevendido/sobrecomprado, score clipado em [-1, 1].",
            "tests/test_classify.py — categoria por palavra-chave, sentimento positivo/negativo/neutro, normalização de acentos.",
            "tests/test_filter.py — detecção por regex (PETR4, VALE3, ITUB4) sem falsos positivos óbvios.",
            "tests/test_score.py — agregação ponderada em janela, ticker inexistente, conjunto vazio.",
            "tests/test_projector.py — direção em torno da zona morta ±0,15, magnitude × confiança, neutro reduz magnitude para 30 %.",
            "tests/test_models.py — init_db idempotente, unique constraints (ticker_id+trade_date, news_id+ticker_id, ticker_id+for_date).",
        ],
        "Critérios de qualidade": [
            "Sem dependência de rede (pytest --offline equivalente).",
            "Tempo total < 5 s.",
            "Cada teste expressa uma asserção clara em seu nome (test_rsi_oversold_below_30, etc.).",
        ],
    }))

    story.append(PageBreak())

    # ---- Fase 3 ----
    story.extend(phase_block(s, 3, "Backtest e métricas de acurácia", {
        "objetivo": "Quantificar empiricamente a qualidade da projeção comparando o que o sistema "
                    "previu com o que de fato aconteceu — fechando a tese central do produto.",
        "esforco": "3 a 5 h",
        "prereq": "Fases 1 e 2 concluídas (dados atualizados e código testado)",
        "aceitacao": "Comando `python -m src.jobs.backtest` produz, no console e em data/backtest_report.json, "
                     "um relatório por ticker com: nº de previsões avaliadas, taxa de acerto direcional, "
                     "MAE da magnitude, distribuição por nível de confiança, e taxa de acerto condicional "
                     "à confiança ≥ 0,5. Página /backtest mostra os números no site.",
    }, {
        "Escopo de trabalho": [
            "Criar src/jobs/backtest.py que percorre todas as predictions e busca o close do for_date no price_daily.",
            "Calcular: direção realizada (sinal de close[for_date] - close[generated_at_date]), magnitude realizada (% return), MAE da magnitude prevista, taxa de acerto direcional global e por ticker.",
            "Exibir métricas estratificadas por nível de confiança (bins 0-0.25, 0.25-0.5, 0.5-0.75, 0.75-1.0).",
            "Criar rota Flask /backtest e template templates/backtest.html com tabela.",
            "Persistir snapshot do relatório em data/backtest_report.json.",
        ],
        "Métricas a reportar": [
            "Acerto direcional global (% das vezes em que direção prevista == realizada, ignorando neutros).",
            "Acerto direcional por ticker.",
            "Acerto condicional: \"Quando o sistema diz alta com confiança ≥ X, qual % das vezes acerta?\".",
            "MAE da magnitude (em pontos percentuais).",
            "Distribuição de previsões por categoria (alta/baixa/neutro) — sanity check de viés.",
            "Comparação com baseline ingênuo (\"sempre alta\" e \"última direção\").",
        ],
        "Arquivos a criar/modificar": [
            "src/jobs/backtest.py (novo)",
            "tests/test_backtest.py (novo)",
            "app.py (adicionar rota /backtest)",
            "templates/backtest.html (novo)",
        ],
    }))

    # ---- Fase 4 ----
    story.extend(phase_block(s, 4, "Scheduler e operação contínua", {
        "objetivo": "Eliminar a operação manual: o pipeline diário deve rodar sozinho em horário "
                    "compatível com o fechamento da B3 e o site precisa expor o status do último ciclo.",
        "esforco": "2 a 3 h",
        "prereq": "Fase 3 concluída (não obrigatório, mas evita publicar métricas vazias)",
        "aceitacao": "Subir o servidor com `python app.py` agenda automaticamente: (a) `daily.run()` "
                     "todos os dias úteis às 19:30 BRT; (b) coleta intermediária de notícias às 12:00 BRT. "
                     "Página inicial exibe \"Última atualização: <timestamp>\" e badge de status (verde/amarelo/vermelho).",
    }, {
        "Escopo de trabalho": [
            "Criar src/jobs/scheduler.py com BackgroundScheduler do APScheduler.",
            "Definir cron jobs: daily.run() em dias úteis (Mon-Fri) 19:30, e ingest_news() ao meio-dia.",
            "Persistir último run_at e último status (success/failed) em uma nova tabela ou em data/runs.json.",
            "Iniciar o scheduler dentro de app.py somente quando __name__ == '__main__' (evitar duplicação no debug-reload).",
            "Adicionar componente visual no topo do site: 'Atualizado em <timestamp>' + indicador colorido.",
            "Logar para arquivo data/logs/scheduler.log com rotação simples.",
        ],
        "Considerações operacionais": [
            "APScheduler em modo Background sobrevive a requests do Flask, mas morre se o processo for encerrado — para servidor 24x7, considerar systemd/Task Scheduler do Windows.",
            "Documentar no CLAUDE.md como iniciar e parar o serviço.",
            "Adicionar variável de ambiente SCHEDULER_DISABLED=1 para rodar o site sem ativar jobs (útil em dev).",
        ],
        "Arquivos a criar/modificar": [
            "src/jobs/scheduler.py (novo)",
            "src/db/models.py (talvez nova tabela run_log)",
            "app.py (instanciar scheduler, exibir status)",
            "templates/base.html (exibir badge de status)",
            "static/css/app.css (estilos do badge)",
        ],
    }))

    story.append(PageBreak())

    # ---- Fase 5 ----
    story.extend(phase_block(s, 5, "Melhorias de UI e observabilidade", {
        "objetivo": "Refinar a experiência do usuário e aumentar a transparência do que o sistema "
                    "está fazendo por baixo dos panos.",
        "esforco": "3 a 4 h",
        "prereq": "Fases 1-4 concluídas",
        "aceitacao": "Usuário consegue, sem instruções, entender (a) por que uma projeção foi alta/baixa/neutra "
                     "olhando o histórico de scores; (b) quais notícias contribuíram e em que direção; "
                     "(c) se os números exibidos são confiáveis (status do pipeline visível).",
    }, {
        "Itens de trabalho": [
            "Gráfico secundário em /ticker/&lt;symbol&gt;: linha temporal do tech_score e bar chart do news_score diário (últimos 60 pregões).",
            "Tooltip explicativo em cada notícia: \"contribuiu +0,12 ao news_score (categoria fundamentos × peso 1,0 × relevância 0,7 × sentimento +0,17)\".",
            "Página /sobre explicando metodologia, fontes e disclaimer (link no footer).",
            "Migrar prints para logging estruturado (logging.getLogger(__name__)) com níveis INFO/WARNING/ERROR.",
            "Adicionar tratamento de exceções no daily.py para que falha em um ticker não derrube os outros.",
            "Deduplicação de URL canonicalizada no filter (remover utm_*, fbclid, ?ref=).",
        ],
        "Arquivos afetados": [
            "templates/ticker.html (gráficos extras + tooltips)",
            "templates/sobre.html (novo)",
            "app.py (rota /sobre, helpers de gráfico)",
            "src/news/filter.py (canonicalização de URL)",
            "src/jobs/daily.py (try/except por ticker)",
            "Vários src/**/*.py (substituir print por logging)",
        ],
    }))

    # ---- Fase 6 ----
    story.extend(phase_block(s, 6, "NLP real para classificação de notícias [opcional]", {
        "objetivo": "Substituir o classificador heurístico por modelos pré-treinados de "
                    "linguagem em português, melhorando a qualidade do news_score.",
        "esforco": "5 a 8 h (mais ~1,5 GB de download de modelos)",
        "prereq": "Fases 1-5 concluídas e baseline de acurácia coletado (Fase 3) para comparação A/B",
        "aceitacao": "Em pipeline paralelo (não substitutivo no primeiro momento), o classificador NLP "
                     "produz score que, comparado pelo backtest, supera o heurístico em ≥ 3 pontos "
                     "percentuais de acerto direcional. Caso não supere, manter o heurístico em produção.",
    }, {
        "Escopo de trabalho": [
            "Descomentar transformers, torch e sentencepiece em requirements.txt.",
            "Substituir classify_category por zero-shot com modelo PT-BR (ex: 'mDeBERTa-v3-base-mnli-xnli').",
            "Substituir score_sentiment por modelo de sentimento PT-BR (ex: 'cardiffnlp/twitter-xlm-roberta-base-sentiment').",
            "Cachear modelos em data/models/ para não baixar a cada run.",
            "Rodar backtest A/B comparando heurístico vs NLP — decidir promoção com base em métricas, não em fé.",
        ],
        "Cuidados": [
            "Pacote final fica grande (PyTorch ~600 MB).",
            "Inferência custa ~50-200 ms por notícia em CPU; aceitável em job diário, não em request síncrono do Flask.",
            "Documentar no CLAUDE.md como ativar/desativar via flag em config.py.",
        ],
    }))

    # ---------- Riscos ----------
    story.append(PageBreak())
    story.append(Paragraph("6. Riscos e mitigações", s["H1"]))
    risk_rows = [
        ["Risco", "Mitigação"],
        ["yfinance ficar instável ou bloquear IP",
         "Backfill/daily fazem retry implícito do urllib3; em produção contínua, considerar fallback para Alpha Vantage ou cache local agressivo. Já existe DELETE+INSERT idempotente."],
        ["RSS retornar volume insuficiente de notícias para news_score significativo",
         "news_score = 0,0 leva o projetor a depender só do tech_score (peso 0,45 vira de fato 1,0 sobre o sinal técnico) — degrada com elegância. Fase 5 inclui canonicalização de URL para reduzir dupes; futuras fases podem adicionar mais feeds."],
        ["Classificador heurístico ter falsos positivos (ex: \"Vale\" referindo-se a ônibus de transporte)",
         "Regex de TICKER_PATTERNS já exige contexto (\"vale s.a.\", \"vale3\", \"mineradora vale\"). Fase 6 com NLP reduz ainda mais."],
        ["Falha em um ticker derrubar o job inteiro",
         "Fase 5 envolve cada ticker em try/except no daily.py."],
        ["Auto-commit publicar dados sensíveis ou estado quebrado",
         ".gitignore já cobre data/, .env, .venv; CLAUDE.md alerta para não terminar turno em estado inconsistente. Considerar pre-commit hook que rode pytest na Fase 2."],
        ["Acurácia ficar abaixo de baseline ingênuo",
         "Backtest da Fase 3 expõe isso explicitamente. Caminhos: ajustar pesos em config.py, expandir conjunto de indicadores, ou aceitar que o sistema é apoio (não preditor)."],
    ]
    t = Table(risk_rows, colWidths=[6.5 * cm, 9.7 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
    ]))
    story.append(t)

    # ---------- Métricas de sucesso ----------
    story.append(Paragraph("7. Métricas de sucesso do projeto", s["H1"]))
    story.append(bullets([
        "<b>Funcional:</b> 100 % das fases 1-4 concluídas com critérios de aceitação atendidos.",
        "<b>Qualidade:</b> ≥ 25 testes passando em &lt; 5 s; cobertura ≥ 80 % nos módulos puros.",
        "<b>Operacional:</b> 7 dias consecutivos com pipeline diário rodando sem intervenção manual.",
        "<b>Métrica de produto (validação):</b> taxa de acerto direcional ≥ 50 % no backtest "
        "(qualquer valor abaixo é aceitável desde que reportado honestamente — o objetivo do "
        "projeto é estudo, não rentabilidade garantida).",
        "<b>Documentação:</b> CLAUDE.md atualizado refletindo qualquer mudança de comando, e README opcional para visitantes externos do GitHub.",
    ], s["Bullet"]))

    # ---------- Roadmap futuro ----------
    story.append(Paragraph("8. Roadmap futuro (pós-MVP)", s["H1"]))
    story.append(Paragraph(
        "Itens fora do escopo do plano atual mas naturalmente conectados — ficam como referência "
        "para uma eventual v2:",
        s["Body"],
    ))
    story.append(bullets([
        "Adição de novos tickers (BBAS3, WEGE3, MGLU3) — só requer entradas em config.TICKERS e re-backfill.",
        "Deploy real (Render, Fly.io ou VPS) com worker separado para o scheduler.",
        "Substituir SQLite por PostgreSQL (2-3 horas de migração com SQLAlchemy).",
        "Treinamento supervisionado: usar histórico de predictions vs realizado como dataset para um classificador próprio (XGBoost ou regressão logística sobre features técnicas + agregados de notícia).",
        "Webhook/Telegram bot para enviar projeções pela manhã.",
        "Integração com fontes de notícias institucionais via API (CVM, B3, releases das próprias empresas).",
        "Modo \"comparar pesos\": UI que permite alterar WEIGHT_NEWS e WEIGHT_TECHNICAL e visualizar impacto retroativo.",
    ], s["Bullet"]))

    # ---------- Apêndice A: comandos ----------
    story.append(PageBreak())
    story.append(Paragraph("Apêndice A — Comandos de referência", s["H1"]))
    story.append(Paragraph(
        "Todos os comandos abaixo assumem que o cwd é a raiz do projeto e usam o "
        "venv local (<i>.venv\\Scripts\\python.exe</i>). A flag <i>-X utf8</i> é "
        "obrigatória no Windows para evitar erro de encoding com caracteres como →, ç, ã.",
        s["Body"],
    ))

    cmd_blocks = [
        ("Setup inicial", "# Instalar dependências\n.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt\n\n# Bootstrap do banco e seed dos tickers\n.\\.venv\\Scripts\\python.exe -X utf8 -c \"from src.db.models import init_db; init_db()\""),
        ("Backfill histórico", ".\\.venv\\Scripts\\python.exe -X utf8 -m src.jobs.backfill"),
        ("Pipeline diário", ".\\.venv\\Scripts\\python.exe -X utf8 -m src.jobs.daily"),
        ("Servidor web", ".\\.venv\\Scripts\\python.exe -X utf8 app.py\n# acesse http://127.0.0.1:5000"),
        ("Testes", ".\\.venv\\Scripts\\python.exe -m pytest                        # todos\n.\\.venv\\Scripts\\python.exe -m pytest tests/test_X.py::test_Y    # único"),
        ("Backtest (Fase 3, ainda a criar)", ".\\.venv\\Scripts\\python.exe -X utf8 -m src.jobs.backtest"),
        ("Regenerar este PDF", ".\\.venv\\Scripts\\python.exe -X utf8 scripts\\generate_plan_pdf.py"),
    ]
    for title, cmd in cmd_blocks:
        story.append(Paragraph(title, s["H3"]))
        story.append(Paragraph(cmd.replace("\n", "<br/>"), s["Code"]))

    # ---------- Apêndice B: estrutura ----------
    story.append(Paragraph("Apêndice B — Estrutura de diretórios", s["H1"]))
    tree = (
        "analise_acoes/\n"
        "├── app.py                         # Flask entrypoint, rotas e filtros Jinja\n"
        "├── config.py                      # Tickers, feeds, regex, pesos, períodos — single source of truth\n"
        "├── requirements.txt               # Dependências (NLP comentado por padrão)\n"
        "├── CLAUDE.md                      # Guia para Claude Code (comandos, convenções, hooks)\n"
        "├── PLANO_EXECUCAO.pdf             # Este documento\n"
        "├── data/\n"
        "│   ├── analise.db                 # SQLite — schema em src/db/models.py (não versionado)\n"
        "│   └── models/                    # Cache de modelos NLP (Fase 6)\n"
        "├── scripts/\n"
        "│   └── generate_plan_pdf.py       # Gera o PDF deste plano\n"
        "├── src/\n"
        "│   ├── db/models.py               # SQLAlchemy: Ticker, PriceDaily, NewsRaw, NewsScored, Prediction\n"
        "│   ├── news/{collect,filter,classify,score}.py\n"
        "│   ├── prices/{fetch,indicators,signal}.py\n"
        "│   ├── prediction/projector.py\n"
        "│   └── jobs/{backfill,daily}.py   # +scheduler.py (Fase 4) +backtest.py (Fase 3)\n"
        "├── templates/\n"
        "│   ├── base.html\n"
        "│   ├── index.html\n"
        "│   └── ticker.html                # +backtest.html (F3) +sobre.html (F5)\n"
        "├── static/css/app.css\n"
        "└── tests/                         # __init__.py + (Fase 2) suite completa\n"
    )
    story.append(Paragraph(tree.replace("\n", "<br/>").replace(" ", "&nbsp;"), s["Code"]))

    # ---------- Apêndice C: fórmulas ----------
    story.append(Paragraph("Apêndice C — Fórmulas-chave do projeto", s["H1"]))
    story.append(Paragraph(
        "Todas as fórmulas estão implementadas em pandas puro (sem pandas-ta). "
        "Os parâmetros são configuráveis via config.py.",
        s["Caption"],
    ))
    formulas = [
        ("RSI (Wilder, período 14)",
         "delta = close.diff()<br/>"
         "gain = delta.clip(lower=0); loss = -delta.clip(upper=0)<br/>"
         "avg_gain = EWM(gain, alpha=1/14); avg_loss = EWM(loss, alpha=1/14)<br/>"
         "RSI = 100 - 100 / (1 + avg_gain / avg_loss)"),
        ("MACD (12, 26, 9)",
         "macd = EMA(close, 12) - EMA(close, 26)<br/>"
         "signal = EMA(macd, 9)<br/>"
         "hist = macd - signal"),
        ("Bollinger (20, 2σ)",
         "mid = SMA(close, 20)<br/>"
         "upper = mid + 2 · STD(close, 20)<br/>"
         "lower = mid - 2 · STD(close, 20)"),
        ("ATR (Wilder, 14)",
         "TR = max( |high - low|, |high - prev_close|, |low - prev_close| )<br/>"
         "ATR = EWM(TR, alpha=1/14)"),
        ("tech_score ∈ [-1, 1]",
         "Soma ponderada de:<br/>"
         " · RSI &lt; 30 → +0,5; RSI &gt; 70 → -0,5; senão linear<br/>"
         " · MACD hist normalizado por close, peso 0,4<br/>"
         " · close vs EMA(21): +0,3 / -0,3<br/>"
         " · breakout das bandas: ±0,2<br/>"
         "Resultado clipado em [-1, 1]."),
        ("news_score ∈ [-1, 1]",
         "Para cada notícia da janela de 48 h:<br/>"
         " · weight = CATEGORY_WEIGHT[cat] × relevance<br/>"
         "news_score = Σ(sentiment × weight) / Σ(weight)"),
        ("Projeção combinada",
         "combined = news_score · 0,55 + tech_score · 0,45<br/>"
         "direction = alta se combined &gt; +0,15; baixa se &lt; -0,15; senão neutro<br/>"
         "confidence = min(|combined|, 1)<br/>"
         "magnitude = ATR% · (0,4 + 0,6 · confidence)<br/>"
         "if neutro: magnitude *= 0,3"),
    ]
    for title, body in formulas:
        story.append(Paragraph(title, s["H3"]))
        story.append(Paragraph(body, s["Code"]))

    return story


def main():
    s = build_styles()
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Plano de Execução — analise_acoes",
        author="Vanderlei Barbosa",
        subject="Plano detalhado para conclusão do projeto analise_acoes",
    )
    doc.build(build_story(s), onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"[ok] PDF gerado em {OUT}")


if __name__ == "__main__":
    main()
