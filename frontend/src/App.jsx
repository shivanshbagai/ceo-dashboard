import React, { useState, useEffect } from 'react';
import {
  Box, Flex, VStack, Text, Heading, SimpleGrid, Card, CardBody,
  Stat, StatLabel, StatNumber, StatHelpText, StatArrow, Input, Button, Spinner, Badge
} from '@chakra-ui/react';
import { LayoutDashboard, MessageSquare, Sparkles, Activity, FileText, Star } from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, Brush
} from 'recharts';
import Favicon from 'react-favicon';

export default function App() {
  // --- View Routing State ---
  const [activeView, setActiveView] = useState("dashboard");

  // --- Data State Management ---
  const [kpis, setKpis] = useState(null);
  const [history, setHistory] = useState([]);

  const [chatInput, setChatInput] = useState("");
  const [chatResponse, setChatResponse] = useState(null);
  const [isChatLoading, setIsChatLoading] = useState(false);

  const [briefing, setBriefing] = useState("");
  const [isBriefingLoading, setIsBriefingLoading] = useState(false);

  // --- Data Fetching on Mount ---
  // Create a reusable fetch function
  const fetchAllData = () => {
    // Optional: Reset state to null to trigger the loading spinners
    setKpis(null);
    setHistory([]);

    fetch("http://127.0.0.1:8000/api/kpis/latest")
      .then(res => res.json())
      .then(data => setKpis(data))
      .catch(err => console.error("KPI Fetch Error:", err));

    fetch("http://127.0.0.1:8000/api/kpis/history")
      .then(res => res.json())
      .then(data => setHistory(data))
      .catch(err => console.error("History Fetch Error:", err));
  };

  // Run it once when the app loads
  useEffect(() => {
    fetchAllData();
  }, []);

  // --- Action Handlers ---
  const fetchBriefing = async () => {
    setIsBriefingLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/briefing");
      const data = await res.json();
      setBriefing(data.briefing);
    } catch (err) {
      console.error(err);
    }
    setIsBriefingLoading(false);
  };

  const handleChatSubmit = async () => {
    if (!chatInput) return;
    setIsChatLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: chatInput })
      });
      const data = await res.json();
      setChatResponse(data);
    } catch (err) {
      console.error(err);
    }
    setIsChatLoading(false);
  };

  // --- Core Design Variables ---
  const theme = {
    bgMain: "#12131A",
    bgCard: "#1C1D24",
    accentPurple: "#B57CFF",
    accentLime: "#D4FF47",
    textPrimary: "#FFFFFF",
    textMuted: "#7E8494",
    borderSubtle: "rgba(255, 255, 255, 0.05)"
  };

  const cardStyle = {
    bg: theme.bgCard,
    border: "none",
    borderRadius: "2xl",
    boxShadow: "0 20px 50px rgba(0,0,0,0.3)",
    transition: "all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
    _hover: {
      transform: 'translateY(-6px)',
      boxShadow: '0 30px 60px rgba(0,0,0,0.5), 0 0 40px rgba(181, 124, 255, 0.1)'
    }
  };

  // Helper function for Sidebar Navigation Items
  const NavItem = ({ id, icon: Icon, label }) => {
    const isActive = activeView === id;
    return (
      <Flex
        as="button"
        w="full"
        align="center"
        gap={3}
        p={3}
        onClick={() => setActiveView(id)}
        bg={isActive ? "rgba(181, 124, 255, 0.1)" : "transparent"}
        borderRadius="xl"
        border="1px solid"
        borderColor={isActive ? "rgba(181, 124, 255, 0.2)" : "transparent"}
        color={isActive ? theme.textPrimary : theme.textMuted}
        _hover={{ color: theme.textPrimary, bg: isActive ? "rgba(181, 124, 255, 0.1)" : "rgba(255,255,255,0.02)" }}
        transition="all 0.2s"
      >
        <Icon size={18} color={isActive ? theme.accentPurple : theme.textMuted} />
        <Text fontWeight="600" fontSize="sm">{label}</Text>
      </Flex>
    );
  };

  return (
    <Flex h="100vh" w="100vw" bg={theme.bgMain} color={theme.textPrimary}>
      <Favicon url="./pngtree-circle-clipart-yellow-circle-png-image_2381940.jpg" />

      {/* Navigation Sidebar */}
      <Box w="260px" bg={theme.bgMain} borderRight="1px solid" borderColor={theme.borderSubtle} p={6} zIndex={10}>
        <Heading size="md" mb={10} tracking="widest" color={theme.textPrimary} display="flex" alignItems="center" gap={2}>
          <Activity color={theme.accentPurple} size={24} />
          CEO <Text as="span" color={theme.accentPurple}>DASHBOARD</Text>
        </Heading>
        <VStack align="stretch" spacing={2}>
          <NavItem id="dashboard" icon={LayoutDashboard} label="Executive View" />
          <NavItem id="briefing" icon={FileText} label="Weekly Briefing" />
          <NavItem id="warehouse" icon={MessageSquare} label="Data Warehouse" />
        </VStack>
      </Box>

      {/* Main Dashboard Canvas */}
      <Flex flex={1} direction="column" overflowY="auto">

        {/* Dynamic Header */}
        <Flex h="80px" align="center" justify="space-between" px={10} borderBottom="1px solid" borderColor={theme.borderSubtle} flexShrink={0}>
          <Heading size="lg" color={theme.textPrimary} fontWeight="700">
            {activeView === "dashboard" && "Financial Overview"}
            {activeView === "briefing" && "AI Chief of Staff Briefing"}
            {activeView === "warehouse" && "Data Warehouse Query Engine"}
          </Heading>

          <Flex align="center" gap={6}>
            {/* New Sync Button */}
            <Button
              size="sm"
              variant="outline"
              borderColor={theme.borderSubtle}
              color={theme.textMuted}
              _hover={{ color: theme.textPrimary, bg: theme.bgCard }}
              onClick={fetchAllData}
            >
              Sync Data
            </Button>

            {activeView === "dashboard" && (
              <Flex align="center" gap={2}>
                <Activity size={16} color={theme.accentLime} />
                <Text fontSize="sm" color={theme.accentLime} fontWeight="bold" letterSpacing="widest">LIVE</Text>
              </Flex>
            )}
          </Flex>
        </Flex>

        <Box p={10} maxW="1400px" mx="auto" w="full">

          {/* ========================================= */}
          {/* VIEW 1: EXECUTIVE VIEW (Dashboard)          */}
          {/* ========================================= */}
          {activeView === "dashboard" && (
            <>
              {/* KPI Strip */}
              {!kpis ? <Spinner size="xl" color={theme.accentPurple} mb={10} /> : (
                <SimpleGrid columns={{ base: 1, md: 4 }} spacing={6} mb={10}>
                  <Card {...cardStyle}>
                    <CardBody p={6}>
                      <Stat>
                        <StatLabel color={theme.textMuted} fontWeight="600" textTransform="uppercase" letterSpacing="wider" mb={2}>Actual Revenue</StatLabel>
                        <Flex justify="space-between" align="flex-end">
                          <StatNumber fontSize="4xl" fontWeight="800" color={theme.textPrimary}>
                            ₹{(kpis.actual_revenue / 1000).toFixed(1)}k
                          </StatNumber>
                          <Badge bg={theme.accentLime} color={theme.bgMain} px={3} py={1} borderRadius="full" fontSize="sm" fontWeight="bold">
                            {kpis.revenue_delta_pct >= 0 ? '+' : ''}{kpis.revenue_delta_pct}%
                          </Badge>
                        </Flex>
                      </Stat>
                    </CardBody>
                  </Card>

                  <Card {...cardStyle}>
                    <CardBody p={6}>
                      <Stat>
                        <StatLabel color={theme.textMuted} fontWeight="600" textTransform="uppercase" letterSpacing="wider" mb={2}>MRR</StatLabel>
                        <StatNumber fontSize="4xl" fontWeight="800" color={theme.textPrimary}>
                          ₹{(kpis.mrr / 1000).toFixed(1)}k
                        </StatNumber>
                      </Stat>
                    </CardBody>
                  </Card>

                  <Card {...cardStyle}>

                    <CardBody p={6}>
                      <Stat>
                        <StatLabel color={theme.textMuted} fontWeight="600" textTransform="uppercase" letterSpacing="wider" mb={2}>Weighted Pipeline</StatLabel>
                        <StatNumber fontSize="4xl" fontWeight="800" color={theme.textPrimary}>
                          ₹{(kpis.pipeline / 1000).toFixed(1)}k
                        </StatNumber>
                      </Stat>
                    </CardBody>
                  </Card>

                  {/* Anti-Gravity CSAT Card */}
                  <Card {...cardStyle}>
                    <CardBody p={6}>
                      <Stat>
                        <Flex justify="space-between" align="flex-start" mb={2}>
                          <StatLabel color={theme.textMuted} fontWeight="600" textTransform="uppercase" letterSpacing="wider">
                            Client Satisfaction
                          </StatLabel>
                          {/* 5-Star Visual Arrangement */}
                          <Flex gap={1} mt={1}>
                            {[1, 2, 3, 4, 5].map(i => (
                              <Star
                                key={i}
                                size={14}
                                fill={i === 5 ? "transparent" : theme.accentLime}
                                color={theme.accentLime}
                                strokeWidth={2}
                              />
                            ))}
                          </Flex>
                        </Flex>
                        <Flex mt-auto mb-80 align="flex-end" >
                          <StatNumber fontSize="4xl" fontWeight="800" color={theme.textPrimary}>
                            4.9<Text as="span" fontSize="xl" color={theme.textMuted}>/5</Text>
                          </StatNumber>

                        </Flex>
                      </Stat>
                    </CardBody>
                  </Card>
                </SimpleGrid>
              )}

              {/* Interactive Chart (With 12-Month Sliding Brush) */}
              <Card {...cardStyle} mb={10}>
                <CardBody p={8}>
                  <Flex justify="space-between" align="center" mb={8}>
                    <Heading size="sm" color={theme.textMuted} textTransform="uppercase" letterSpacing="wider">Revenue Performance (History)</Heading>
                    <Badge bg="rgba(181, 124, 255, 0.2)" color={theme.accentPurple} px={3} py={1} borderRadius="full" fontSize="xs">
                      Target Adjusted
                    </Badge>
                  </Flex>

                  {/* Increased height slightly to accommodate the new timeline slider */}
                  <Box h="400px" w="full">
                    {history.length === 0 ? (
                      <Flex h="100%" align="center" justify="center"><Spinner color={theme.accentPurple} /></Flex>
                    ) : (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={history} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                          <defs>
                            <linearGradient id="glowPurple" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={theme.accentPurple} stopOpacity={0.4} />
                              <stop offset="95%" stopColor={theme.accentPurple} stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="glowLime" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={theme.accentLime} stopOpacity={0.2} />
                              <stop offset="95%" stopColor={theme.accentLime} stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.borderSubtle} />

                          {/* minTickGap ensures labels don't overlap if you zoom all the way out */}
                          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 12 }} dy={10} minTickGap={20} />
                          <YAxis tickFormatter={(val) => `₹${val / 1000}k`} axisLine={false} tickLine={false} tick={{ fill: theme.textMuted, fontSize: 12 }} dx={-10} />

                          <Tooltip
                            contentStyle={{ backgroundColor: theme.bgCard, borderColor: theme.borderSubtle, borderRadius: '12px', color: theme.textPrimary }}
                            itemStyle={{ color: theme.textPrimary }}
                            formatter={(value) => [`₹${value.toLocaleString()}`, undefined]}
                          />
                          <Legend iconType="circle" verticalAlign="top" wrapperStyle={{ paddingBottom: '20px', color: theme.textMuted }} />

                          <Area type="monotone" dataKey="target_revenue" name="Target" stroke={theme.accentPurple} strokeWidth={2} fillOpacity={1} fill="url(#glowPurple)" />
                          <Area type="monotone" dataKey="actual_revenue" name="Actual" stroke={theme.accentLime} strokeWidth={2} fillOpacity={1} fill="url(#glowLime)" />

                          {/* The Timeline Slider - Defaults to the last 12 months */}
                          <Brush
                            dataKey="month"
                            height={40}
                            stroke={theme.accentPurple}
                            fill={theme.bgMain}
                            travellerWidth={10}
                            startIndex={Math.max(0, history.length - 12)}
                            tickFormatter={() => ''}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    )}
                  </Box>
                </CardBody>
              </Card>
            </>
          )}

          {/* ========================================= */}
          {/* VIEW 2: WEEKLY BRIEFING                   */}
          {/* ========================================= */}
          {activeView === "briefing" && (
            <Card {...cardStyle} minH="60vh">
              <CardBody p={10}>
                <Flex justify="space-between" align="center" mb={10} borderBottom="1px solid" borderColor={theme.borderSubtle} pb={6}>
                  <Flex align="center" gap={4}>
                    <Box p={3} bg="rgba(181, 124, 255, 0.1)" borderRadius="xl" color={theme.accentPurple} border="1px solid" borderColor="rgba(181, 124, 255, 0.2)">
                      <Sparkles size={24} />
                    </Box>
                    <Box>
                      <Heading size="md" color={theme.textPrimary}>Latest Briefing Synthesis</Heading>
                      <Text fontSize="sm" color={theme.textMuted} mt={1}>Automated multi-department data analysis</Text>
                    </Box>
                  </Flex>

                  <Button
                    size="md"
                    bg={theme.accentPurple}
                    color={theme.bgMain}
                    _hover={{ bg: "#c89dff" }}
                    onClick={fetchBriefing}
                    isLoading={isBriefingLoading}
                    loadingText="Analyzing Data..."
                    fontWeight="bold"
                    borderRadius="full"
                    px={8}
                  >
                    {briefing ? "Regenerate" : "Generate Briefing"}
                  </Button>
                </Flex>

                <Box sx={{ whiteSpace: "pre-wrap" }} color={theme.textPrimary} fontSize="lg" lineHeight="1.8">
                  {briefing ? briefing : (
                    <Flex direction="column" align="center" justify="center" h="200px" color={theme.textMuted}>
                      <Text>No briefing generated yet.</Text>
                      <Text fontSize="sm">Click the button above to run the AI analysis.</Text>
                    </Flex>
                  )}
                </Box>
              </CardBody>
            </Card>
          )}

          {/* ========================================= */}
          {/* VIEW 3: DATA WAREHOUSE                    */}
          {/* ========================================= */}
          {activeView === "warehouse" && (
            <Card {...cardStyle} minH="60vh">
              <CardBody p={10}>
                <Heading size="md" color={theme.textPrimary} mb={2}>Natural Language Query</Heading>
                <Text color={theme.textMuted} mb={8}>Type a plain-English question to securely query the underlying SQLite database.</Text>

                <Flex gap={4}>
                  <Input
                    size="lg"
                    bg="transparent"
                    color={theme.textPrimary}
                    placeholder="e.g. Which project has the highest billable hours?"
                    _placeholder={{ color: theme.textMuted }}
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleChatSubmit()}
                    borderRadius="xl"
                    border="1px solid"
                    borderColor={theme.borderSubtle}
                    _focus={{ borderColor: theme.accentPurple, boxShadow: `0 0 0 1px ${theme.accentPurple}` }}
                  />
                  <Button
                    size="lg"
                    bg={theme.accentPurple}
                    color={theme.bgMain}
                    _hover={{ bg: "#c89dff" }}
                    borderRadius="xl"
                    px={10}
                    onClick={handleChatSubmit}
                    isLoading={isChatLoading}
                    fontWeight="bold"
                  >
                    Run Query
                  </Button>
                </Flex>

                {chatResponse && (
                  <Box mt={10} p={8} bg="rgba(0,0,0,0.2)" borderRadius="2xl" border="1px" borderColor={theme.borderSubtle}>
                    <Text fontWeight="800" color={theme.accentLime} mb={4} fontSize="xl">Executive Summary</Text>
                    <Text color={theme.textPrimary} fontSize="lg" mb={8} lineHeight="tall">
                      {chatResponse.answer}
                    </Text>

                    {/* Dark Mode Data Table */}
                    {chatResponse.data && chatResponse.data.length > 0 && (
                      <Box overflowX="auto" border="1px" borderColor={theme.borderSubtle} borderRadius="xl" bg={theme.bgMain}>
                        <Box as="table" width="full" textAlign="left">
                          <Box as="thead" bg={theme.bgCard} borderBottom="1px" borderColor={theme.borderSubtle}>
                            <Box as="tr">
                              {Object.keys(chatResponse.data[0]).map((key) => (
                                <Box as="th" key={key} p={4} fontSize="xs" textTransform="uppercase" color={theme.textMuted} fontWeight="700" letterSpacing="wider">
                                  {key.replace(/_/g, ' ')}
                                </Box>
                              ))}
                            </Box>
                          </Box>
                          <Box as="tbody">
                            {chatResponse.data.map((row, i) => (
                              <Box as="tr" key={i} _hover={{ bg: "rgba(255,255,255,0.02)" }} transition="background 0.2s">
                                {Object.values(row).map((val, j) => (
                                  <Box
                                    as="td"
                                    key={j}
                                    p={4}
                                    fontSize="sm"
                                    color={theme.textPrimary}
                                    fontWeight="500"
                                    borderBottom="1px solid"
                                    borderColor={theme.borderSubtle}
                                  >
                                    {val}
                                  </Box>
                                ))}
                              </Box>
                            ))}
                          </Box>
                        </Box>
                      </Box>
                    )}
                  </Box>
                )}
              </CardBody>
            </Card>
          )}

        </Box>
      </Flex>
    </Flex>
  );
}