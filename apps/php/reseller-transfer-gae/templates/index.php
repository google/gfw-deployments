<?php
    include '_header.html';
?>

    <h1>Transfer a customer</h1>

    <form action="/transfer" method="POST">
        <p class="maia-note">
            Domain
            <input type="text" name="customerDomain">
        </p>
        <p class="maia-note">
            Transfer Token
            <input type="text" name="customerAuthToken">
        </p>
        <p class="maia-note">
            Number number of users accounts (soft cap)
            <input type="text" name="numberOfSeats" value="10">
        </p>
        <p class="maia-note">
            Maximum number of users (hard cap)
            <input type="text" name="maximumNumberOfSeats" value="15">

        </p>
        <input type="submit" class="maia-button">
    </form>

<?
    include '_footer.html';
?>