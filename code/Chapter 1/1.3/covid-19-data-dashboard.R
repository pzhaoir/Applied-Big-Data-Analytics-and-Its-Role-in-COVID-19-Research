library(shiny)
library(shinydashboard)
library(shinySIR)
library("devtools")
library(DT)


us_covid_data <- read.csv("https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv")
mySIRS <- function(t, y, parms) {
  
  with(as.list(c(y, parms)),{
    
    # Change in Susceptibles
    dS <- - beta * S * I + delta * R
    
    # Change in Infecteds
    dI <- beta * S * I - gamma * I
    
    # Change in Recovereds
    dR <- gamma * I - delta * R
    
    return(list(c(dS, dI, dR)))
  })
}

ui <- dashboardPage(
  dashboardHeader(title = "COVID-19 Dashboard"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("COVID-19-US-Data", tabName = "COVID-19-US-Data"),
      menuItem("SIR", tabName = "SIR"),
      menuItem("SIR", tabName = "SIRS")
    )
  ),
  dashboardBody(
    tabItems(
      tabItem("COVID-19",
              fluidPage(
                h1("COVID-19-US-Data"),
                DT::dataTableOutput("covidtable")
              )
      ),
      tabItem("SIR",
              run_shiny(model = "SIR")),
      tabItem("SIRS", 
              run_shiny(model = "SIRS", 
                        neweqns = mySIRS,
                        ics = c(S = 9999, I = 1, R = 0),
                        parm0 = c(beta = 5e-5, gamma = 1/7, delta = 0.1),
                        parm_names = c("Transmission rate", "Recovery rate", "Loss of immunity"),
                        parm_min = c(beta = 1e-5, gamma = 1/21, delta = 1/365),
                        parm_max = c(beta = 9e-5, gamma = 1 , delta = 1)))
      )
    )
  )


server <- function(input, output){
  output$covidtable <- DT::renderDataTable({DT::datatable(us_covid_data)})
}
shinyApp(ui, server)