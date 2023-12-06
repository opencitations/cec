declare namespace x = "net.researchgate.xml";
declare namespace saxon="http://saxon.sf.net/";
declare namespace xsl="http://www.w3.org/1999/XSL/Transform";


declare function x:vector-intersect($el1, $g) {
    let $bx1 := min(($g/*/@x,$g/*/@x1,$g/*/@x2, $g/*/@x3))
    let $by1 := min(($g/*/@y,$g/*/@y1,$g/*/@y2, $g/*/@y3))
    let $bx2 := max(($g/*/@x,$g/*/@x1,$g/*/@x2, $g/*/@x3))
    let $by2 := max(($g/*/@y,$g/*/@y1,$g/*/@y2, $g/*/@y3))

    let $ax1 := number($el1/@x)
    let $ay1 := number($el1/@y)
    let $ax2 := number($el1/@x) + number($el1/@width)
    let $ay2 := number($el1/@y) + number($el1/@height)

    return
        if ($ax2 < $bx1) then false() else
            if ($ax1 > $bx2) then false() else
                if ($ay2 < $by1) then false() else
                    if ($ay1 > $by2) then false() else
                        true()
};

declare function x:intersect($el1, $el2) {
    let $ax1 := number($el1/@HPOS)
    let $ay1 := number($el1/@VPOS)
    let $ax2 := number($el1/@HPOS) + number($el1/@WIDTH)
    let $ay2 := number($el1/@VPOS) + number($el1/@HEIGHT)

    let $bx1 := number($el2/@HPOS)
    let $by1 := number($el2/@VPOS)
    let $bx2 := number($el2/@HPOS) + number($el2/@WIDTH)
    let $by2 := number($el2/@VPOS) + number($el2/@HEIGHT)

    return
        if ($ax2 < $bx1) then false() else
            if ($ax1 > $bx2) then false() else
                if ($ay2 < $by1) then false() else
                    if ($ay1 > $by2) then false() else
                        true()
};

declare function x:coords($el1) {
    let $ax1 := number($el1/@HPOS)
    let $ay1 := number($el1/@VPOS)
    let $ax2 := number($el1/@HPOS) + number($el1/@WIDTH)
    let $ay2 := number($el1/@VPOS) + number($el1/@HEIGHT)
    return
        concat($ax1, ";", $ay1, ";", $ax2, ";",$ay2, ";")
};

declare function x:error($msg) {
    error(QName('http://researchgate.net/err', 'VectorGraphicsDetected'), $msg)
};

declare function x:process-doc($doc) {
    let $res :=
        for $p in $doc//Page return
        let $page-num := xs:integer($p/@number) return
        if (count($p//Illustration) > 10) then ($page-num, concat("Too many images on page ", $p/@number)) else
          for $i in $p//Illustration return
            let $imgs := $doc//*[@x][./@id != $i/@id][./ancestor::Page/@number = $i/ancestor::Page/@number][ x:intersect($i, .)]

            return
                if ($imgs) then
                    ($page-num, string-join(("Page: ", $p/@number, " ", $i, x:coords($i), $imgs/(./@href/string(), x:coords(.))), " "))
                else
                    let $vect := $doc//Illustration/GROUP[./ancestor::Page/@number = $i/ancestor::Page/@number][x:vector-intersect($i, .)] return
                    if ($vect) then
                        ($page-num, concat("VECT!", $i/ancestor::Page/@number, '; ',
                            saxon:serialize($vect[1],
                            <xsl:output method="xml"
                            omit-xml-declaration="yes"
                            indent="yes"
                            saxon:indent-spaces="1"/>), ";;;", x:coords($i), count($vect))
                        )
                else ()
    return
        $res
        (:let $join := string-join($res, "; ") return:)
            (:if (string-length($join) = 0) then () else $res:)
        (:if (empty($res)) then:)
            (:fn:true():)
        (:else:)
            (:fn:false():)


};

x:process-doc(/)