function brl(value) {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function crypto_email(name,price, buy_price, target) {
    const url = SpreadsheetApp.getActiveSpreadsheet().getUrl();
    const ganho = ((price / buy_price - 1) * 100).toFixed(1);
    return `
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
      <div style="background:#1a7f37;color:#fff;padding:16px 20px">
        <div style="font-size:13px;opacity:.85">Alerta de preço</div>
        <div style="font-size:22px;font-weight:bold">${name} atingiu o alvo </div>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:15px">
        <tr><td style="padding:12px 20px;color:#666">Preço atual</td>
            <td style="padding:12px 20px;text-align:right;font-weight:bold">${brl(price)}</td></tr>
        <tr style="background:#f7f7f7"><td style="padding:12px 20px;color:#666">Preço alvo</td>
            <td style="padding:12px 20px;text-align:right">${brl(target)}</td></tr>
        <tr><td style="padding:12px 20px;color:#666">Preço de compra</td>
            <td style="padding:12px 20px;text-align:right">${brl(buy_price)}</td></tr>
        <tr style="background:#f7f7f7"><td style="padding:12px 20px;color:#666">Valorização</td>
            <td style="padding:12px 20px;text-align:right;color:#1a7f37;font-weight:bold">+${ganho}%</td></tr>
      </table>
      <div style="padding:20px;text-align:center">
        <a href="${url}" style="background:#1a7f37;color:#fff;text-decoration:none;padding:10px 20px;border-radius:6px;display:inline-block">Abrir planilha</a>
      </div>
    </div>`;
}
function crypto_prices_check(){
  const email = "";
  const name_collum = 2;
  const price_collum = 8;
  const target_collum = 7;
  const status_collum = 9;
  const buy_price_collum = 4;
  var crypto_tab = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("CRIPTO");
  var last_row = crypto_tab.getLastRow()
  for(var i = 3 ; i <= last_row; i++) {
    var name = crypto_tab.getRange(i, name_collum).getValue();
    var price = crypto_tab.getRange(i, price_collum).getValue();
    var target = crypto_tab.getRange(i, target_collum).getValue();
    var status = crypto_tab.getRange(i, status_collum).getValue();
    var buy_price = crypto_tab.getRange(i, buy_price_collum).getValue();

    if(status == "NOTIFICADO") {
      if(price < target) {
        crypto_tab.getRange(i, status_collum).clearContent();
      }
      continue;
    }

    if (price >= target && target > 0) {
      MailApp.sendEmail(
        email,
         `Seu preço de venda de cripto de ${name} foi atingido`,
         `${name} atingiu seu preço de venda. Atual: ${brl(price)} | Alvo: ${brl(target)}`,
         { htmlBody: crypto_email(name, price, buy_price, target) }
         );
      crypto_tab.getRange(i, status_collum).setValue("NOTIFICADO");
    }
  }
}
