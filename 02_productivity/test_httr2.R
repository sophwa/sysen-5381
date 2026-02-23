#' @name test_httr2.R
#' @title GET Request with httr2
#' @description
#' Topic: HTTP API Requests
#'
#' Demonstration of making a GET request to the GitHub API using httr2.
#' Uses request() to create the request, then req_perform() to execute it.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

library(httr2) # for HTTP requests

# 1. MAKE GET REQUEST ###################################

# Create request and perform it in one pipeline
# httr2 uses GET by default when no body is added
resp = request("https://api.github.com/users/octocat") %>%
  req_perform()

# 2. INSPECT RESPONSE ###################################

# Check status (200 = success)
resp_status(resp)
resp_status_desc(resp)

# Parse JSON body into an R list
resp %>%
  resp_body_json()
