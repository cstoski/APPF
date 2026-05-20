/**

 * Serial de licença: 16 caracteres alfanuméricos em grupos XXXX-XXXX-XXXX-XXXX.

 * Gerado pelo fornecedor com tools/gerar_licenca.py para o HWID do equipamento.

 */



export function formatarSerialLicencaGrupos(value) {

  const alnum = String(value || '')

    .replace(/[^A-Za-z0-9]/g, '')

    .toUpperCase()

    .slice(0, 16)

  const partes = []

  for (let i = 0; i < alnum.length; i += 4) {

    partes.push(alnum.slice(i, i + 4))

  }

  return partes.join('-')

}



export function exibirSerialLicenca(serial) {

  if (!serial) return '—'

  return formatarSerialLicencaGrupos(serial)

}



export function serialLicencaCompletoParaEnvio(valorCampo) {

  return formatarSerialLicencaGrupos(valorCampo)

}


