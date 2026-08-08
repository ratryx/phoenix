/* ============================================================
   Phoenix Optimizer — Histórico (v2)
   ============================================================ */

(function (Phoenix) {
    "use strict";

    const page = {};

    Phoenix.pages = Phoenix.pages || {};
    Phoenix.pages.historico = page;

    page.load = async function () {
        var container = document.getElementById("conteudo-historico");
        if (!container) return;

        container.innerHTML =
            '<p class="texto-secundario">Carregando histórico...</p>';
        Phoenix.ui.feedback.mostrarOverlay("Consultando histórico...");

        try {
            var resultado = await Phoenix.bridge.call("obter_historico");
            Phoenix.ui.feedback.esconderOverlay();

            if (!resultado) { 
                return; 
            }

            if (!resultado.ok) {
                container.innerHTML = "";
                var card = document.createElement("div");
                card.className = "card";
                var badge = document.createElement("span");
                badge.className = "badge erro";
                badge.textContent = "Erro";
                card.appendChild(badge);
                card.appendChild(document.createTextNode(" " + (resultado.erro || "Erro desconhecido")));
                container.appendChild(card);
                return;
            }

            if (!resultado.atendimentos || resultado.atendimentos.length === 0) {
                container.innerHTML = "";
                var p = document.createElement("p");
                p.className = "texto-secundario";
                p.textContent = "Nenhum atendimento registrado ainda.";
                container.appendChild(p);
                return;
            }

            container.innerHTML = "";
            var card = document.createElement("div");
            card.className = "card";
            var table = document.createElement("table");
            table.className = "tabela-dados";
            var thead = document.createElement("thead");
            var headerRow = document.createElement("tr");
            ["ID", "Cliente", "Data/Hora"].forEach(text => {
                var th = document.createElement("th");
                th.textContent = text;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);
            
            var tbody = document.createElement("tbody");
            resultado.atendimentos.forEach(a => {
                var tr = document.createElement("tr");
                [a.id_atendimento, a.cliente, a.data_hora].forEach(val => {
                    var td = document.createElement("td");
                    td.textContent = val;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            card.appendChild(table);
            container.appendChild(card);
        } catch (err) {
            console.error("[ERRO] Histórico:", err);
            Phoenix.ui.feedback.esconderOverlay();
        }
    };

})(window.Phoenix);
