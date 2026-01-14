<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns="http://www.tei-c.org/ns/1.0"
    xmlns:math="http://www.w3.org/1998/Math/MathML"
    exclude-result-prefixes="#all">

  <xsl:output method="xml" indent="yes"/>
  <xsl:strip-space elements="*"/>

  <!-- Root template - figures first, then tables -->
  <xsl:template match="/">
    <TEI>
      <text>
        <body>
          <!-- First: process all non-figure, non-table content -->
          <xsl:apply-templates select="article/body/*[not(self::fig or self::table-wrap)]"/>

          <!-- Second: process all figures (images) -->
          <xsl:apply-templates select="article/body//fig" mode="end"/>

          <!-- Third: process all tables -->
          <xsl:apply-templates select="article/body//table-wrap" mode="end"/>

          <!-- Process footnotes eventually -->
          <xsl:apply-templates select="article/back//fn-group[not(@*)]" mode="end"/>
        </body>
        <back>
           <!-- Data Availability -->
          <xsl:apply-templates select="article/back//sec[@sec-type='data-availability']"/>

          <!-- Acknowledgments -->
          <xsl:apply-templates select="article/back//ack"/>

        </back>
      </text>
    </TEI>
  </xsl:template>

  <!-- DIV -->
  <xsl:template match="sec">
  <div>
    <!-- Add sec-type attribute if present -->
    <xsl:if test="@sec-type">
      <xsl:attribute name="type">
         <xsl:choose>
          <xsl:when test="@sec-type = 'data-availability'">availability</xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="@sec-type"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="title">
      <!-- normalize title once -->
      <xsl:variable name="t" select="normalize-space(title)"/>

      <!-- analyze-string using a portable XML Schema regex (no \b, no lookarounds) -->
      <xsl:analyze-string select="$t" regex="^([0-9]+(\.[0-9]+)*\.?)(.*)$">
        <xsl:matching-substring>
          <!-- regex-group(1) is the number (e.g. 2.3.1) -->
          <xsl:variable name="num" select="regex-group(1)"/>
          <!-- regex-group(3) is the rest of the title-->
          <xsl:variable name="rest" select="regex-group(3)"/>
          <head>
            <xsl:attribute name="n">
              <xsl:value-of select="normalize-space($num)"/>
            </xsl:attribute>
            <xsl:value-of select="normalize-space($rest)"/>
          </head>
        </xsl:matching-substring>

        <xsl:non-matching-substring>
          <!-- no leading number — output title as-is -->
          <head>
            <xsl:value-of select="$t"/>
          </head>
        </xsl:non-matching-substring>
      </xsl:analyze-string>
    </xsl:if>

    <xsl:apply-templates select="node() except title"/>
  </div>
  </xsl:template>

  <!-- Acknowledgment -->
  <xsl:template match="ack">
    <div type="acknowledgement">
    <xsl:if test="title">
      <head>
        <xsl:value-of select="normalize-space(title)"/>
      </head>
    </xsl:if>
    <xsl:apply-templates select="node() except title"/>
    </div>
  </xsl:template>


  <!-- Handle paragraphs -->
  <xsl:template match="p">
    <p>
      <!-- Copy text nodes up to the first formula -->
      <xsl:apply-templates select="node()[not(self::inline-formula or self::disp-formula)]"/>
    </p>

    <!-- Process formulas separately -->
    <xsl:apply-templates select="inline-formula | disp-formula"/>
  </xsl:template>

  <!-- Handle inline formulas -->
  <xsl:template match="inline-formula">
    <formula type="inline">
      <xsl:if test="@id">
        <xsl:attribute name="id">
          <xsl:value-of select="@id"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="math:math"/>
    </formula>
    <!-- Start a new paragraph for following text -->
    <xsl:if test="not(following-sibling::*[1][self::p])">
    <p>
      <xsl:apply-templates select="following-sibling::node()[not(self::inline-formula or self::disp-formula)]"/>
    </p>
    </xsl:if>
  </xsl:template>

  <!-- Handle display formulas -->
  <xsl:template match="disp-formula">
    <formula type="display">
      <xsl:if test="@id">
        <xsl:attribute name="id">
          <xsl:value-of select="@id"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="math:math"/>
    </formula>
    <xsl:if test="not(following-sibling::*[1][self::p])">
    <p>
      <xsl:apply-templates select="following-sibling::node()[not(self::inline-formula or self::disp-formula)]"/>
    </p>
    </xsl:if>
  </xsl:template>


  <xsl:template match="italic|bold|sup|sub|underline|strike|sc">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="xref">
    <ref>
      <xsl:attribute name="type">
        <xsl:choose>
          <xsl:when test="@ref-type = 'table'">table</xsl:when>
          <xsl:when test="@ref-type = 'bibr'">bibr</xsl:when>
          <xsl:when test="@ref-type = 'fig'">figure</xsl:when>
          <xsl:when test="@ref-type = 'other' and starts-with(@rid, 'FN')">foot</xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="@ref-type"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <xsl:attribute name="target">
        <xsl:text>#</xsl:text><xsl:value-of select="@rid"/>
      </xsl:attribute>
      <xsl:apply-templates/>
    </ref>
  </xsl:template>

  <xsl:template match="ext-link">
    <ref type="external" target="{@xlink:href}">
      <xsl:apply-templates/>
    </ref>
  </xsl:template>


  <!-- Copy MathML elements without prefixes and extra namespaces -->
  <xsl:template match="math:*">
    <xsl:element name="{local-name()}">
      <!-- Copy only relevant attributes (id, display, etc.) -->
      <xsl:for-each select="@*">
        <xsl:if test="not(starts-with(name(), 'xmlns')) and name() != 'overflow'">
          <xsl:attribute name="{name()}">
            <xsl:value-of select="."/>
          </xsl:attribute>
        </xsl:if>
      </xsl:for-each>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>


  <xsl:template match="list">
    <list>
      <xsl:apply-templates/>
    </list>
  </xsl:template>

  <xsl:template match="list-item">
    <item>
      <xsl:if test="label">
        <xsl:value-of select="label"/>
      </xsl:if>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="p"/>

    </item>
  </xsl:template>

  <!-- ========================================================= -->
  <!-- fn-group main switch based on structure                   -->
  <!-- ========================================================= -->
  <xsl:template match="fn-group" mode="end">

      <xsl:choose>
        <!-- Case 1: multiple fn → one note per fn -->
        <xsl:when test="count(fn) > 1">
            <xsl:apply-templates select="fn" mode="fn-multi"/>
        </xsl:when>

        <!-- Case 2: one fn with multiple p[@id] → split notes -->
        <xsl:when test="count(fn) = 1 and count(fn/p[@id]) > 1">
            <xsl:apply-templates select="fn/p[@id]" mode="p-as-note"/>
        </xsl:when>

        <!-- Case 4: single fn with its own id (even if p[@id] missing) -->
        <xsl:when test="count(fn) = 1 and fn[@id]">
            <xsl:apply-templates select="fn" mode="fn-single"/>
        </xsl:when>

        <!-- Case 3: standalone p inside fn-group -->
        <xsl:when test="count(p[@id]) > 0">
            <xsl:apply-templates select="p[@id]" mode="p-as-note"/>
        </xsl:when>

        <xsl:otherwise/>
      </xsl:choose>

  </xsl:template>

  <!-- Case 1: multiple fn → note per fn -->
  <xsl:template match="fn" mode="fn-multi">
      <note type="foot" xml:id="{@id | p[@id][1]/@id}">
          <xsl:apply-templates select="p"/>
      </note>
  </xsl:template>

  <!-- Case 2 + 3: each p → one note -->
  <xsl:template match="p" mode="p-as-note">
      <note type="foot" xml:id="{@id}">
        <p>
          <xsl:apply-templates/>
        </p>
      </note>
  </xsl:template>

  <!-- Case 4: single fn with its own id -->
  <xsl:template match="fn" mode="fn-single">
      <note type="foot" xml:id="{@id}">
          <xsl:apply-templates select="p"/>
      </note>
  </xsl:template>


  <!-- SUPPRESS normal figure and table processing -->
  <xsl:template match="fig | table-wrap"/>

  <!-- Figure template for end mode -->
  <xsl:template match="fig" mode="end">
    <figure>

      <xsl:if test="@id">
        <xsl:attribute name="xml:id">
          <xsl:value-of select="@id"/>
        </xsl:attribute>
      </xsl:if>

      <head>
        <xsl:value-of select="normalize-space(label)"/>
      </head>

      <label>
        <xsl:value-of select="replace(label, '^[^0-9]*([0-9]+).*$', '$1')"/>
      </label>

      <figDesc>
        <xsl:value-of select="caption"/>
      </figDesc>

      <xsl:apply-templates select="graphic"/>
    </figure>
  </xsl:template>

  <xsl:template match="graphic">
    <graphic url="{@xlink:href}">
      <xsl:if test="@orientation">
        <xsl:attribute name="orientation">
          <xsl:value-of select="@orientation"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@position">
        <xsl:attribute name="position">
          <xsl:value-of select="@position"/>
        </xsl:attribute>
      </xsl:if>
    </graphic>
  </xsl:template>

  <!-- Table-wrap template for end mode -->
  <xsl:template match="table-wrap" mode="end">
    <figure type="table">
      <xsl:attribute name="xml:id">
        <xsl:value-of select="@id"/>
      </xsl:attribute>

      <head>
        <xsl:value-of select="normalize-space(label)"/>
      </head>

      <label>
        <xsl:value-of select="replace(label, '^[^0-9]*([0-9]+).*$', '$1')"/>
      </label>

      <figDesc>
        <xsl:value-of select="caption"/>
      </figDesc>

      <xsl:apply-templates select="table"/>

      <xsl:apply-templates select="table-wrap-foot"/>
    </figure>
  </xsl:template>

    <!-- Convert table - skip thead/tbody but process their content -->
    <xsl:template match="table">
        <table>
            <!-- Process all content of thead and tbody but skip the elements themselves -->
            <xsl:apply-templates select="thead/node() | tbody/node()"/>
        </table>
    </xsl:template>

    <xsl:template match="table-wrap-foot">
      <xsl:for-each select="fn/p">
        <note>
          <xsl:if test="@id">
            <xsl:attribute name="xml:id">
              <xsl:value-of select="@id"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:apply-templates/>
        </note>
      </xsl:for-each>
    </xsl:template>

  <xsl:template match="thead | tbody">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="tr[parent::thead]">
    <row role="label">
      <xsl:apply-templates/>
    </row>
  </xsl:template>

  <xsl:template match="tr[parent::tbody]">
    <row>
      <xsl:apply-templates/>
    </row>
  </xsl:template>

  <xsl:template match="th|td">
    <cell>
      <xsl:if test="number(@rowspan) &gt; 1">
        <xsl:attribute name="rowspan">
          <xsl:value-of select="@rowspan"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="number(@colspan) &gt; 1">
        <xsl:attribute name="colspan">
          <xsl:value-of select="@colspan"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </cell>
  </xsl:template>

  <xsl:template match="break">
    <xsl:text> </xsl:text>
  </xsl:template>


  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>



</xsl:stylesheet>