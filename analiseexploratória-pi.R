#• Mineração de dados – padrões
# objeto processo
install.packages("jsonlite") 
install.packages("dplyr")
library(jsonlite)
library(dplyr)

dados.mainframe

# Pegar o texto da coluna com os processos
processos_txt <- dados.mainframe$processos
#Substituir aspas simples por aspas duplas para formar JSON válido
processos_txt_corrigido <- gsub("'", '"', processos_txt)
#Converter para lista R
processos_lista <- fromJSON(processos_txt_corrigido)


#distribuicao<-sample(dados.mainframe,size = 500,replace = TRUE) comando para distribuir os dados com base em csv já existente


################distribuindo dados######################

# Garantir que timestamp é POSIXct (mantém tipo de data)
 dados.mainframe$timestamp<-as.POSIXct(
  dados.mainframe$timestamp,
  format = "%d-%m-%Y %H:%M:%S",
  tz = "America/Sao_Paulo"
)

# Número de novas linhas
n_novas_linhas <- 500

# Amostra com reposição
amostra <- dados.mainframe[sample(1:nrow(dados.mainframe), size = n_novas_linhas, replace = TRUE), ]

# Ordenar
amostra <- amostra[order(amostra$timestamp), ]

# Criar timestamps novos variando de hora em hora
ultimo_tempo <- max(dados.mainframe$timestamp)
amostra$timestamp <- seq(from = ultimo_tempo + 3600, by = 3600, length.out = n_novas_linhas)

# Juntar tudo
dados.expandidos <- rbind(dados.mainframe, amostra)

#  formata a data sem o fuzo horário
dados.expandidos$timestamp<-format(dados.expandidos$timestamp, "%d-%m-%Y %H:%M:%S")
dados.expandidos$timestamp

# Visualizar resultado
head(dados.expandidos, 10)
tail(dados.expandidos, 10)



#• Gráfico/Dashboard/Ranking

#• Definição das métricas (Dimensões)

#• Definição de Alertas
#>90% processador <5%
#>85% memoria
#>90% usodisco 
#>rankeando os maiores processos
#>cpu tempo
#>hist cpu, 
#hist ram,
#processos q mais gastam recursos, 
#media uso recurso por dia\mês\ano?
#fazer uma curva linear de previsão de gasto de recurso. 
#tentar prever perdas conforme documentação. 
#processos que estão aumentando ou diminuindo seu uso com o tempo? 
  