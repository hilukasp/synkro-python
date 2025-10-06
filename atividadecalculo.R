install.packages("ggplot2")
library(ggplot2)


df<-dados.mainframe

#iops= a soma de quantidade de clusters lidos ou escritos (operações)  
#throughtput_mbs= volume de dados transferidos por segundo

#Relação iops disco e ler
#relação forte
cor(df$disco_iops_total, df$disco_read_count)
plot(df$disco_iops_total, df$disco_read_count)
ggplot(mapping = aes(df$disco_iops_total, df$disco_read_count)) +
  geom_point(color = "red") +
  geom_smooth(method = "lm", color = "green")

#Relação iops disco e escrever
#relação forte
cor(df$disco_iops_total, df$disco_write_count)
plot(df$disco_iops_total, df$disco_write_count)
ggplot(mapping = aes(df$disco_iops_total, df$disco_write_count)) +
  geom_point(color = "red") +
  geom_smooth(method = "lm", color = "green")

  
#Relação entre volume de dados transferidos por segundo e quantidade de operações por segundo
#relação fraca
#o IOPS ele é quantificado por cluster lido ou escrito, ou seja o IOPS não necessariamente segue em linearidade com o throughput
#Arquivos pequenos → mesmo throughput, mais IOPS (muitas operações pequenas)
#Arquivos grandes → mesmo throughput, menos IOPS (leitura sequencial mais eficiente)
cor(df$disco_throughput_mbs,df$disco_iops_total)
ggplot(mapping = aes(df$disco_throughput_mbs, df$disco_iops_total)) +
  geom_point(color = "red") +
  geom_smooth(method = "lm", color = "green")
 

#Relação de escrever e ler
#relação fraca
cor(df$disco_write_count, df$disco_read_count)
ggplot(mapping = aes(df$disco_write_count, df$disco_read_count)) +
  geom_point(color = "red") +
  geom_smooth(method = "lm", color = "green")

#relação entre RAM e CPU
#correlação fraca
cor(df$disco_throughput_mbs,df$uso_cpu_total_.)
ggplot(mapping = aes(df$uso_ram_total_., df$uso_cpu_total_.)) +
  geom_point(color = "red") +
  geom_smooth(method = "lm", color = "green")


boxplot(df$disco_read_count,
        df$disco_write_count,
        df$disco_iops_total,
        names = c("Read", "Write", "IOPS"),
        col = c("lightblue", "lightgreen", "lightpink"),
        main = "Utilização de disco"
)

boxplot(df$uso_cpu_total_.,
        main = "Uso de CPU Total (%)",
        ylab = "Porcentagem"
        )
boxplot(df$uso_ram_total_.,
        main = "Uso de RAM Total (%)",
        ylab = "Porcentagem"
        )
boxplot(df$uso_disco_total_.,
        main = "Uso de Disco Total (%)",
        ylab = "Porcentagem"
        )