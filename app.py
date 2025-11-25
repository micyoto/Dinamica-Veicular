import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Trab 02 - Dinâmica Veicular", layout="wide", page_icon="🚗")

# --- CABEÇALHO E APRESENTAÇÃO ---
st.title("🚗 Simulador de Dinâmica Veicular (Jazar - Cap. 2)")
st.subheader("Análise do Chevrolet Onix Plus 2026")

st.markdown("""
**Trabalho 02 - Dinâmica Longitudinal**

**Integrantes do Grupo:**
- Gabriel Monteiro
- Lucas Sander Guimarães Silva
- Michael Yoshiaki Todoroki

Esta ferramenta simula as reações nos pneus baseada nas equações de **Reza N. Jazar**.
Use o menu lateral para configurar o veículo e as abas abaixo para ver os cenários.

A configuração default é baseada no **Chevrolet Onix Plus 2026**.
""")

# --- FICHA TÉCNICA (MOVIDA PARA O CORPO PRINCIPAL) ---
with st.expander("📄 Ver Ficha Técnica: Chevrolet Onix Plus 2026 (Dados utilizados)", expanded=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown("""
        **Especificações Técnicas:**
        - **Modelo:** Onix Plus Premier 1.0 Turbo
        - **Massa Total ($m$):** 1117 kg
        - **Entre-eixos ($l$):** 2.60 m
        """)
    with col_f2:
        st.markdown("""
        **Geometria e Peso:**
        - **Bitola ($w$):** 1.508 m
        - **Altura do CG ($h$):** 0.54 m (Estimado)
        - **Distribuição de Peso:** 60% Dianteira / 40% Traseira
        """)
    st.caption("*Fonte: Manual do Proprietário / Fichas Técnicas Automotivas*")

st.divider() # Linha divisória para separar a intro da simulação

# ==========================================
# 2. CLASSE DO VEÍCULO (LÓGICA MATEMÁTICA)
# ==========================================
class Veiculo:
    def __init__(self, m, l, h, w, dist_front_pct):
        self.m = m              # Massa (kg)
        self.g = 9.81           # Gravidade
        self.L = l              # Entre-eixos (m)
        self.h = h              # Altura CG (m)
        self.w = w              # Bitola (m)
        
        # Cálculo das distâncias do CG aos eixos
        self.a2 = (dist_front_pct / 100.0) * self.L # Distância CG -> Eixo Traseiro
        self.a1 = self.L - self.a2                  # Distância CG -> Eixo Dianteiro

    def get_loads_longitudinal(self, ax, angulo_graus):
        phi = np.radians(angulo_graus)
        W = self.m * self.g
        
        # Termo Estático com Inclinação (Jazar 2.16 e 2.17)
        term_front_stat = 0.5 * W * ( (self.a2 / self.L) * np.cos(phi) - (self.h / self.L) * np.sin(phi) )
        term_rear_stat  = 0.5 * W * ( (self.a1 / self.L) * np.cos(phi) + (self.h / self.L) * np.sin(phi) )
        
        # Transferência de carga por aceleração (Jazar 2.25 e 2.26)
        transf = 0.5 * self.m * ax * (self.h / self.L)
        
        Fz1 = term_front_stat - transf
        Fz2 = term_rear_stat + transf
        
        return max(0, Fz1), max(0, Fz2)

    def get_loads_lateral(self, angulo_bank):
        phi = np.radians(angulo_bank)
        W = self.m * self.g
        b1 = self.w / 2
        b2 = self.w / 2
        
        # Jazar Seção 2.5
        Fz_baixo = 0.5 * (W / self.w) * (b2 * np.cos(phi) + self.h * np.sin(phi))
        Fz_cima  = 0.5 * (W / self.w) * (b1 * np.cos(phi) - self.h * np.sin(phi))
        
        return max(0, Fz_baixo), max(0, Fz_cima)

# ==========================================
# 3. SIDEBAR - APENAS INPUTS AGORA
# ==========================================
st.sidebar.header("⚙️ Ajuste de Parâmetros")
st.sidebar.info("Modifique os valores abaixo para simular outros cenários ou veículos.")

# Inputs com os valores default do Onix
m_input = st.sidebar.number_input("Massa ($m$) [kg]", value=1117.0, step=10.0)
l_input = st.sidebar.number_input("Entre-eixos ($l$) [m]", value=2.60, step=0.01)
h_input = st.sidebar.number_input("Altura do CG ($h$) [m]", value=0.54, step=0.01)
w_input = st.sidebar.number_input("Bitola ($w$) [m]", value=1.508, step=0.01)
dist_input = st.sidebar.slider("Peso na Dianteira (%)", 40, 70, 60)

# Instanciando o objeto carro com os dados da sidebar
carro = Veiculo(m_input, l_input, h_input, w_input, dist_input)

# Mostra resultado do cálculo geométrico na sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Geometria Calculada:**\n- $a_1$ (CG-Frente): {carro.a1:.2f} m\n- $a_2$ (CG-Trás): {carro.a2:.2f} m")

# ==========================================
# 4. ÁREA PRINCIPAL - ABAS DE SIMULAÇÃO
# ==========================================

# Criando as abas
tab1, tab2, tab3 = st.tabs(["⛰️ Rampa (Inclinado)", "🚀 Aceleração Longitudinal", "🏎️ Inclinação Lateral"])

# --- TAB 1: RAMPA ---
with tab1:
    st.header("1. Veículo em Rampa (Jazar 2.2)")
    
    st.info("Equações Governantes (Parked Car on an Inclined Road):")
    st.latex(r'''
    F_{z1} = \frac{1}{2} W \left( \frac{a_2}{l} \cos \theta - \frac{h}{l} \sin \theta \right) 
    \quad | \quad 
    F_{z2} = \frac{1}{2} W \left( \frac{a_1}{l} \cos \theta + \frac{h}{l} \sin \theta \right)
    ''')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Parâmetros")
        angle_input = st.slider("Ângulo da Rampa ($\theta$) [graus]", 0, 45, 0)
        
        fz1, fz2 = carro.get_loads_longitudinal(0, angle_input)
        
        st.markdown("### Resultados Pontuais")
        st.metric("Eixo Dianteiro ($F_{z1}$)", f"{fz1:.1f} N")
        st.metric("Eixo Traseiro ($F_{z2}$)", f"{fz2:.1f} N")
    
    with col2:
        angles = np.linspace(0, 45, 50)
        res_fz1 = [carro.get_loads_longitudinal(0, a)[0] for a in angles]
        res_fz2 = [carro.get_loads_longitudinal(0, a)[1] for a in angles]
            
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(angles, res_fz1, label='$F_{z1}$ (Dianteiro)', color='blue', linewidth=2)
        ax.plot(angles, res_fz2, label='$F_{z2}$ (Traseiro)', color='red', linewidth=2)
        
        ax.scatter([angle_input], [fz1], color='blue', s=80, zorder=5)
        ax.scatter([angle_input], [fz2], color='red', s=80, zorder=5)
        
        ax.set_xlabel(r"Ângulo da Rampa $\theta$ (graus)")
        ax.set_ylabel("Força Normal (N)")
        ax.set_title("Variação da Carga Normal com a Inclinação")
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()
        st.pyplot(fig)

# --- TAB 2: ACELERAÇÃO ---
with tab2:
    st.header("2. Aceleração Longitudinal (Jazar 2.3/2.4)")
    
    st.info("Equações Governantes (Accelerating Car):")
    st.latex(r'''
    F_{z1} = F_{z1_{estático}} - \frac{1}{2} \frac{m a_x h}{l} 
    \quad | \quad 
    F_{z2} = F_{z2_{estático}} + \frac{1}{2} \frac{m a_x h}{l}
    ''')
    
    col_a1, col_a2 = st.columns([1, 2])
    
    with col_a1:
        st.markdown("### Parâmetros")
        accel_input = st.slider("Aceleração ($a_x$) [$m/s^2$]", 0.0, 10.0, 3.0, step=0.1)
        
        # Opção extra de rampa combinada
        ramp_accel = st.checkbox("Simular em subida?", value=False)
        angle_accel = st.number_input("Ângulo da subida", 0, 30, 5) if ramp_accel else 0
            
        fz1_a, fz2_a = carro.get_loads_longitudinal(accel_input, angle_accel)
        
        st.markdown("### Resultados")
        st.metric("Eixo Dianteiro ($F_{z1}$)", f"{fz1_a:.1f} N")
        st.metric("Eixo Traseiro ($F_{z2}$)", f"{fz2_a:.1f} N")
        
        if fz1_a <= 0:
            st.error("⚠️ PERDA DE CONTATO (EMPINOU)")
    
    with col_a2:
        accels = np.linspace(0, 10, 50)
        res_fz1_a = [carro.get_loads_longitudinal(ac, angle_accel)[0] for ac in accels]
        res_fz2_a = [carro.get_loads_longitudinal(ac, angle_accel)[1] for ac in accels]
            
        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        ax2.plot(accels, res_fz1_a, label='$F_{z1}$ (Dianteiro)', color='blue', linewidth=2)
        ax2.plot(accels, res_fz2_a, label='$F_{z2}$ (Traseiro)', color='red', linewidth=2)
        ax2.axhline(0, color='black', linewidth=1)
        
        ax2.scatter([accel_input], [fz1_a], color='blue', s=80)
        ax2.scatter([accel_input], [fz2_a], color='red', s=80)

        title_suffix = f" (Subida {angle_accel}°)" if angle_accel > 0 else " (Plano)"
        ax2.set_title(f"Transferência de Carga por Aceleração{title_suffix}")
        ax2.set_xlabel(r"Aceleração Longitudinal $a_x$ ($m/s^2$)")
        ax2.set_ylabel("Força Normal (N)")
        ax2.grid(True, linestyle='--', alpha=0.6)
        ax2.legend()
        st.pyplot(fig2)

# --- TAB 3: LATERAL ---
with tab3:
    st.header("3. Inclinação Lateral / Banked Road (Jazar 2.5)")
    
    st.info("Equações Governantes:")
    st.latex(r'''
    F_{zi} = \frac{1}{2} \frac{W}{w} (b \cos \phi \pm h \sin \phi)
    ''')
    
    bank_input = st.slider("Ângulo Lateral ($\phi$) [graus]", 0, 60, 0)
    fz_low, fz_high = carro.get_loads_lateral(bank_input)
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.metric("Pneus de Baixo (Lado da queda)", f"{fz_low:.1f} N")
    with col_l2:
        st.metric("Pneus de Cima (Lado elevado)", f"{fz_high:.1f} N")
    
    if fz_high <= 0:
        st.error("⚠️ VEÍCULO TOMBOU LATERALMENTE!")
            
    fig3, ax3 = plt.subplots(figsize=(6, 2.5))
    bars = ax3.bar(["Lado Baixo", "Lado Cima"], [fz_low, fz_high], color=['green', 'orange'])
    ax3.set_title(f"Distribuição Lateral para Inclinação de {bank_input}°")
    ax3.set_ylabel("Força (N)")
    ax3.set_ylim(0, max(fz_low, fz_high)*1.2)
    st.pyplot(fig3)

# Rodapé final
st.markdown("---")
st.caption("Desenvolvido por Gabriel Monteiro, Lucas Sander Guimarães Silva e Michael Yoshiaki Todoroki.\n")
st.caption("Fonte dos modelos matemáticos: Reza N. Jazar - 'Vehicle Dynamics: Theory and Application' (2nd Edition).")
st.caption("Dados do veículo: Manual do Proprietário Chevrolet Onix Plus 2026.")
st.caption("Ferramenta desenvolvida para fins acadêmicos na disciplina de Dinâmica Veicular.")
st.caption("2024 © Todos os direitos reservados.")
# st.caption("Universidade Federal de Tecnologia - Disciplina de Dinâmica Veicular")