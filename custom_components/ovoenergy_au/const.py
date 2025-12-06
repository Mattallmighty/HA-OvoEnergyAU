"""Constants for the OVO Energy Australia integration."""

from datetime import timedelta

# Integration domain
DOMAIN = "ovoenergy_au"

# Configuration and options
CONF_ACCOUNT_ID = "account_id"

# Auth0 / OAuth2 constants
AUTH_BASE_URL = "https://login.ovoenergy.com.au"
API_BASE_URL = "https://my.ovoenergy.com.au"
GRAPHQL_URL = f"{API_BASE_URL}/graphql"

OAUTH_CLIENT_ID = "5JHnPn71qgV3LmF3I3xX0KvfRBdROVhR"
OAUTH_AUTHORIZE_URL = f"{AUTH_BASE_URL}/authorize"
OAUTH_TOKEN_URL = f"{AUTH_BASE_URL}/oauth/token"
OAUTH_LOGIN_URL = f"{AUTH_BASE_URL}/usernamepassword/login"
OAUTH_SCOPES = ["openid", "profile", "email", "offline_access"]
OAUTH_AUDIENCE = f"{AUTH_BASE_URL}/api"
OAUTH_CONNECTION = "prod-myovo-auth"  # Auth0 database connection name
OAUTH_REDIRECT_URI = f"{API_BASE_URL}?login=oea"

# Update intervals
# Poll daily at 2am since data is only available for yesterday
UPDATE_INTERVAL = timedelta(hours=24)
UPDATE_HOUR = 2  # 2am daily
FAST_UPDATE_INTERVAL = timedelta(minutes=5)  # For manual refresh

# Sensor types
SENSOR_TYPES = {
    "solar_consumption": {
        "name": "Solar Consumption",
        "unit": "kWh",
        "icon": "mdi:solar-power",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "export_consumption": {
        "name": "Export Consumption",
        "unit": "kWh",
        "icon": "mdi:transmission-tower-export",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    "solar_charge": {
        "name": "Solar Charge",
        "unit": "$",
        "icon": "mdi:currency-usd",
        "device_class": "monetary",
        "state_class": "total",
    },
    "export_charge": {
        "name": "Export Charge",
        "unit": "$",
        "icon": "mdi:currency-usd",
        "device_class": "monetary",
        "state_class": "total",
    },
}

# GraphQL queries
GET_CONTACT_INFO_QUERY = """
query GetContactInfo($input: GetContactInfoInput!) {
  GetContactInfo(input: $input) {
    accounts {
      id
      number
      customerId
      customerOrientatedBalance
      closed
      system
      hasSolar
      supplyAddress {
        buildingName
        buildingName2
        lotNumber
        flatType
        flatNumber
        floorType
        floorNumber
        houseNumber
        houseNumber2
        houseSuffix
        houseSuffix2
        streetSuffix
        streetName
        streetType
        suburb
        state
        postcode
        countryCode
        country
        addressType
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

GET_INTERVAL_DATA_QUERY = """
query GetIntervalData($input: GetIntervalDataInput!) {
  GetIntervalData(input: $input) {
    daily {
      ...UsageV2DataParts
      __typename
    }
    monthly {
      ...UsageV2DataParts
      __typename
    }
    yearly {
      ...UsageV2DataParts
      __typename
    }
    __typename
  }
}

fragment UsageV2DataParts on UsageV2Data {
  solar {
    periodFrom
    periodTo
    consumption
    readType
    charge {
      value
      type
      __typename
    }
    __typename
  }
  export {
    periodFrom
    periodTo
    consumption
    readType
    charge {
      value
      type
      __typename
    }
    __typename
  }
  __typename
}
"""

GET_HOURLY_DATA_QUERY = """
query GetHourlyData($input: GetHourlyDataInput!) {
  GetHourlyData(input: $input) {
    ...UsageV2DataParts
    __typename
  }
}

fragment UsageV2DataParts on UsageV2Data {
  solar {
    periodFrom
    periodTo
    consumption
    readType
    charge {
      value
      type
      __typename
    }
    __typename
  }
  export {
    periodFrom
    periodTo
    consumption
    readType
    charge {
      value
      type
      __typename
    }
    __typename
  }
  __typename
}
"""

# Error messages
ERROR_AUTH_FAILED = "Authentication failed. Please check your credentials."
ERROR_CANNOT_CONNECT = "Cannot connect to OVO Energy API."
ERROR_INVALID_AUTH = "Invalid authentication."
ERROR_UNKNOWN = "Unknown error occurred."
