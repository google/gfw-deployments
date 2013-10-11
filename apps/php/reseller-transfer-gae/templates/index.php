<?php
    include '_header.html';
?>

    <h1>Transfer a customer</h1>

    <form action="/transfer" method="POST">
        Domain
        <input type="text" name="customerDomain">
        Transfer Token
        <input type="text" name="customerAuthToken">
        <input type="submit" class="maia-button">
    </form>

<?
    include '_footer.html';
?>