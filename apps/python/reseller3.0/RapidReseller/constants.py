#!/usr/bin/python
#
# Copyright 2013 Google Inc. All Rights Reserved.

"""
      DISCLAIMER:

   (i) GOOGLE INC. ("GOOGLE") PROVIDES YOU ALL CODE HEREIN "AS IS" WITHOUT ANY
   WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING,
   WITHOUT LIMITATION, ANY IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A
   PARTICULAR PURPOSE AND NON-INFRINGEMENT; AND

   (ii) IN NO EVENT WILL GOOGLE BE LIABLE FOR ANY LOST REVENUES, PROFIT OR DATA,
   OR ANY DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
   DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF
   GOOGLE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES, ARISING OUT OF
   THE USE OR INABILITY TO USE, MODIFICATION OR DISTRIBUTION OF THIS CODE OR
   ITS DERIVATIVES.
   """

__author__ = 'richieforeman@google.com (Richie Foreman)'


class ResellerSKU(object):
    '''
    A class of constants containing various Enterprise SKUs.

    src: https://developers.google.com/admin-sdk/reseller/v1/how-tos/products
    '''

    GoogleApps = "Google-Apps-For-Business"
    GoogleDriveStorage20GB = "Google-Drive-storage-20GB"
    GoogleDriveStorage50GB = "Google-Drive-storage-50GB"
    GoogleDriveStorage200GB = "Google-Drive-storage-200GB"
    GoogleDriveStorage400GB = "Google-Drive-storage-400GB"
    GoogleDriveStorage1TB = "Google-Drive-storage-1TB"
    GoogleDriveStorage2TB = "Google-Drive-storage-2TB"
    GoogleDriveStorage4TB = "Google-Drive-storage-4TB"
    GoogleDriveStorage8TB = "Google-Drive-storage-8TB"
    GoogleDriveStorage16TB = "Google-Drive-storage-16TB"
    GoogleVault = "Google-Vault"

class ResellerPlanName(object):
    # Traditional annual agreement.
    Annual = "ANNUAL"

    # Month-to-Month
    Flexible = "FLEXIBLE"

    # 30 Day (max) trial.
    Trial = "TRIAL"

class ResellerRenewalType(object):
    # automatically renew for the same license count.
    AutoRenew = "AUTO_RENEW"

    # automatically renew for the current user count (for better or worse)
    RenewCurrent = "RENEW_CURRENT_USERS"

    # at the renewal date, switch to a "FLEXIBLE" plan type,
    # which is billed on a monthly basis.
    PayAsYouGo = "SWITCH_TO_PAY_AS_YOU_GO"

    # at the renewal date, cancel the subscription
    Cancel = "CANCEL"