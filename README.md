# 🚗 TopCar ERP - Manual de Operação e Fluxos de Negócio

---

## 💻 VISÃO GERAL DO SISTEMA

O TopCar ERP é uma solução de gestão completa, projetada com foco em **integridade financeira** e **rastreabilidade de custos por veículo (ROI)**, utilizando Python/Django e a reatividade do HTMX.

O sistema garante que cada ação (compra, manutenção, venda) seja uma **transação atômica**, evitando inconsistências contábeis. Foi validado com cenários de troca, troco (saldo negativo) e lançamentos de despesas gerais.

---

## 🚀 GUIA DE ACESSO RÁPIDO

### Acesso ao Sistema
* **URL de Teste (Docker):** `http://localhost:8000/`
* **Usuário de Teste:** `admin_teste`
* **Senha de Teste:** `123`

### Fluxo de Validação Crítico (PoC)
| AÇÃO NO SISTEMA | EFEITO NO ESTOQUE | EFEITO FINANCEIRO |
| :--- | :--- | :--- |
| **1. Nova Aquisição** | Status: **MAINTENANCE** | Gera **Contas a Pagar (Ledger)** |
| **2. Oficina (Custo)** | Status: MAINTENANCE | Gera **Contas a Pagar** (Mecânico) |
| **3. Venda C/ Troca** | Carro Vendido → **SOLD** / Carro Troca → **MAINTENANCE** | Gera **Contas a Receber** OU **Contas a Pagar (Troco)** |
| **4. Quitação** | Sem alteração | Altera **Saldo** da Conta Bancária (Cash Flow) |
| **5. Cancelamento** | Carro Vendido → **AVAILABLE** / Carro Troca → **DELETADO** | Ledger (Conta) → **CANCELED** (Estorno) |

---

## ⚙️ FLUXOS DE NEGÓCIO ESSENCIAIS

### 1. FLUXO DE AQUISIÇÃO E PREPARAÇÃO (Custo Real)
Este fluxo insere o carro no estoque e atribui a ele o custo real:

* **Ação A:** Menu **Veículos** ➕ **Nova Aquisição**.
    * **Resultado:** Cria o veículo no Estoque e gera uma **Conta a Pagar (Ledger)** para o Fornecedor.
* **Ação B:** Menu **Oficina 🔧** (Nova OS).
    * **Resultado:** Cria uma Ordem de Serviço, que, ao ser concluída, gera uma **Conta a Pagar** separada para o Mecânico (custo atrelado ao Veículo para o cálculo do ROI).

### 2. FLUXO DE VENDA E LIQUIDAÇÃO
* **Capacidade:** Permite venda simples ou **Venda com Troca**, calculando o saldo (positivo ou negativo) na hora.
* **Ação B (Baixa):** Menu **Financeiro** (Contas a Pagar/Receber).
    * **Resultado:** Permite **Quitar** (Baixar) a Conta. Ao quitar, o saldo do Banco/Caixa é atualizado e o item sai da lista de abertos.

### 3. FLUXO DE AUDITORIA E CORREÇÃO
* **Cancelamento:** Na tela Detalhes da Venda, o botão **Cancelar / Estornar Venda** reverte a transação atomicamente, devolvendo o carro vendido para o status **AVAILABLE** e deletando o carro da troca (garantindo que o histórico financeiro seja marcado como **CANCELED**).

---

## 📊 RELATÓRIOS E AUDITORIA

O sistema oferece as seguintes ferramentas de inteligência gerencial:

### 1. Relatório de Lucro (ROI)
* **Acesso:** Menu **Veículos 🚗** 📈 Relatório de Lucro (ROI).
* **Função:** Cruza todos os lançamentos atrelados a um veículo (Aquisição, Manutenção, Venda) e exibe o **Lucro Líquido Real** do chassi.

### 2. Lançamentos Manuais (Flexibilidade Total)
* **Acesso:** Menu **Financeiro 💸** → Contas a Pagar/Receber → **+ Novo Lançamento Manual**.
* **Função:** Permite registrar **despesas avulsas** (Ex: Conta de Luz) ou **Bônus/Comissões variáveis** sem atrelar a um carro, usando categorias (Plano de Contas).

---

## 🛠️ ESTRUTURA DE NAVEGAÇÃO (Menu Principal)

| MÓDULO | URL | AÇÕES PRINCIPAIS |
| :--- | :--- | :--- |
| **Dashboard** | `/` | Visão Geral, KPIs e Atividade Recente. |
| **Cadastros** | Dropdown | Gestão de Pessoas (**Clientes**, **Colaboradores**) e Domínio (**Marcas**, **Modelos**). |
| **Veículos** | Dropdown | **Estoque**, **Nova Aquisição**, **Relatório ROI** (Lucro). |
| **Vendas** | Dropdown | **Nova Venda** (com Troca) e **Histórico** (com Estorno). |
| **Financeiro** | Dropdown | **Contas a Pagar/Receber**, **Extrato**, **Plano de Contas** (Config). |
| **Oficina** | `/maintenance/` | Gestão de Ordens de Serviço (OS) e Custos de Preparação. |