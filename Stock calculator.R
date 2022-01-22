# This is the Piotrotski f-score calculator that I use myself.
# The web scrape code is adapted from sample codes by QHarr:
# https://stackoverflow.com/questions/58315274/r-web-scraping-yahoo-finance-after-2019-change


library(tidyverse)
library(rvest)
library(stringr)
library(magrittr)
library(data.table)
library(lubridate)
setwd("C:/Users/Tguan/Desktop/Random R projects/Stock Market")

# Find the ticker symbol of company and insert here:
output<- f_score("AAPL")


f_score<- function(ticker){

urlis<- paste0("https://sg.finance.yahoo.com/quote/",ticker,"/financials?p=",ticker)
urlbs<- paste0("https://sg.finance.yahoo.com/quote/",ticker,"/balance-sheet?p=",ticker)
urlcf<- paste0("https://sg.finance.yahoo.com/quote/",ticker,"/cash-flow?p=",ticker)
    
is<- read_html(urlis)
bs<- read_html(urlbs)
cf<- read_html(urlcf)

#Income Statement Webscrape

isnodes <- is %>%html_nodes(".fi-row")
isdf = NULL

for(i in isnodes){
  isr <- list(i %>%html_nodes("[title],[data-test='fin-col']")%>%html_text())
  isdf <- rbind(isdf,as.data.frame(matrix(isr[[1]], ncol = length(isr[[1]]), byrow = TRUE), stringsAsFactors = FALSE))
}

matches <- str_match_all(is%>%html_node('#Col1-1-Financials-Proxy')%>%html_text(),'\\d{1,2}/\\d{1,2}/\\d{4}')  
headers <- c('Breakdown','TTM', matches[[1]][,1]) 
names(isdf) <- headers

#Balance Sheet Webscrape

bsnodes <- bs %>%html_nodes(".fi-row")
bsdf = NULL

for(i in bsnodes){
  bsr <- list(i %>%html_nodes("[title],[data-test='fin-col']")%>%html_text())
  bsdf <- rbind(bsdf,as.data.frame(matrix(bsr[[1]], ncol = length(bsr[[1]]), byrow = TRUE), stringsAsFactors = FALSE))
}

matches <- str_match_all(bs%>%html_node('#Col1-1-Financials-Proxy')%>%html_text(),'\\d{1,2}/\\d{1,2}/\\d{4}')  
headers <- c('Breakdown', matches[[1]][,1]) 
names(bsdf) <- headers

#Cash flow statement Webscrape
cfnodes <- cf %>%html_nodes(".fi-row")
cfdf = NULL

for(i in cfnodes){
  cfr <- list(i %>%html_nodes("[title],[data-test='fin-col']")%>%html_text())
  cfdf <- rbind(cfdf,as.data.frame(matrix(cfr[[1]], ncol = length(cfr[[1]]), byrow = TRUE), stringsAsFactors = FALSE))
}

matches <- str_match_all(cf%>%html_node('#Col1-1-Financials-Proxy')%>%html_text(),'\\d{1,2}/\\d{1,2}/\\d{4}')  
headers <- c('Breakdown','TTM', matches[[1]][,1]) 
names(cfdf) <- headers

#Clean dataset
isdf<- isdf %>%
  t() %>%
  as.data.frame()

colnames(isdf)<- slice(isdf, 1)
isdf<- isdf %>%
  slice(-1)

isdf$date<- rownames(isdf)
isdf<- isdf %>%
  select(date, everything()) %>%
  sapply( function(v) {gsub("\\,","", as.character(v))})


bsdf<- bsdf %>%
  t() %>%
  as.data.frame()

colnames(bsdf)<- slice(bsdf, 1)
bsdf<- bsdf %>%
  tail(-1)

bsdf$date<- rownames(bsdf)
colnames(bsdf)[first(which(names(bsdf) == "Deferred revenues"))]<- 
  "Current deferred revenue"
bsdf<- bsdf %>%
  select(date, everything()) %>%
  sapply( function(v) {gsub("\\,","", as.character(v))})

cfdf<- cfdf %>%
  t() %>%
  as.data.frame()

colnames(cfdf)<- slice(cfdf, 1)
colnames(cfdf)[first(which(names(cfdf) == "Free cash flow"))]<- 
  "Free cash flow calculations"
cfdf<- cfdf %>%
  slice(-1)

cfdf$date<- rownames(cfdf)
cfdf<- cfdf %>%
  select(date, everything()) %>%
  sapply( function(v) {gsub("\\,","", as.character(v))})

# Append dataset
df1<- isdf %>%
  as.data.frame() %>%
  inner_join(as.data.frame(bsdf), by ="date") %>%
  inner_join(as.data.frame(cfdf), by = "date")


df_dates<- df1 %>%
  select(date) %>%
  as.matrix() %>%
  dmy() %>%
  as.data.frame()

colnames(df_dates)<- "date"


f_list<- df1 %>%
  sapply(as.numeric) %>%
  as.data.frame() %>%
  transmute(c.net_income = ifelse(`Net income.x` > 0, 1, 0),
            c.roa = ifelse((`Net income.x`/`Total assets`) > 0, 1, 0),
            c.ocf = ifelse(`Net cash provided by operating activities` >0, 1, 0),
            ocf_roa_comp = ifelse(`Net cash provided by operating activities` >
                                    `Net income.x`, 1, 0),
            c.debt = ifelse((`Total non-current liabilities`/`Total assets`) < 
                              lead((`Total non-current liabilities`/`Total assets`)),
                            1 , 0),
            c.current_ratio = ifelse((`Total current assets`/`Total current liabilities`) >
                                       lead(`Total current assets`/`Total current liabilities`),
                                     1, 0),
            shares_issued = ifelse( `Common stock` != lead(`Common stock`),
                                    1,0),
            c.profit_margin = ifelse((`Gross profit`/`Total revenue`) > 
                                       lead(`Gross profit`/`Total revenue`),
                                     1, 0),
            c.asset_turnover = ifelse((`Total revenue`/`Total assets`) >
                                        lead(`Total revenue`/`Total assets`),
                                      1, 0)
  )

f_list<- cbind(df_dates, f_list)

f_list<- f_list %>%
  mutate(total = c.net_income + c.roa + c.ocf + ocf_roa_comp + c.debt +
           c.current_ratio + shares_issued + c.profit_margin + 
           c.asset_turnover,
         f_score = ifelse(total == 8 | total == 9, "Good Investment",
                          "Bad Investment")) %>%
  slice(1) %>%
  select(f_score, total, everything())
}
