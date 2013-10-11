<?php

class ResellerSKU {
    const GoogleApps = "Google-Apps-For-Business";
    const GoogleDriveStorage20GB = "Google-Drive-storage-20GB";
    const GoogleDriveStorage50GB = "Google-Drive-storage-50GB";
    const GoogleDriveStorage200GB = "Google-Drive-storage-200GB";
    const GoogleDriveStorage400GB = "Google-Drive-storage-400GB";
    const GoogleDriveStorage1TB = "Google-Drive-storage-1TB";
    const GoogleDriveStorage2TB = "Google-Drive-storage-2TB";
    const GoogleDriveStorage4TB = "Google-Drive-storage-4TB";
    const GoogleDriveStorage8TB = "Google-Drive-storage-8TB";
    const GoogleDriveStorage16TB = "Google-Drive-storage-16TB";
    const GoogleVault = "Google-Vault";
}

class ResellerPlanName {

    // Annual plan
    const ANNUAL = "ANNUAL";

    // Month-to-month plan
    const FLEXIBLE = "FLEXIBLE";

    // Trial plan.
    const TRIAL = "TRIAL";
}

class ResellerRenewalType {
    // automatically renew for the same license count purchased.
    const AUTO_RENEW = "AUTO_RENEW";

    // automatically renew for the current user count (for better or worse)
    const RENEW_CURRENT = "RENEW_CURRENT_USERS";

    // at the renewal date, switch to a "FLEXIBLE" plan type,
    // which is billed on a monthly basis.
    // This is only relevant when adjusting an annual plan.
    const PAY_AS_YOU_GO = "SWITCH_TO_PAY_AS_YOU_GO";

    // at the renewal date, cancel the subscription
    const CANCEL = "CANCEL";
}

?>